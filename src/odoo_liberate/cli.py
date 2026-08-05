import argparse
import os
import sys
import zipfile
import shutil
import tempfile
import subprocess

def run_psql_command(db_kwargs, sql_query, verbose=True):
    """Executes a SQL query against the specified PostgreSQL database using the psql CLI."""
    env = os.environ.copy()
    if db_kwargs.get('password'):
        env['PGPASSWORD'] = db_kwargs['password']
    
    cmd = ['psql', '-q', '-v', 'ON_ERROR_STOP=1']
    
    if db_kwargs.get('host'):
        cmd.extend(['-h', db_kwargs['host']])
    if db_kwargs.get('port'):
        cmd.extend(['-p', str(db_kwargs['port'])])
    if db_kwargs.get('user'):
        cmd.extend(['-U', db_kwargs['user']])
    
    cmd.extend(['-d', db_kwargs['dbname']])
    
    if verbose:
        print(f"Executing: {sql_query.strip().splitlines()[0][:60]}...")
        
    try:
        result = subprocess.run(cmd, input=sql_query.encode('utf-8'), env=env, check=True, capture_output=True)
        if verbose and result.stdout:
            print(result.stdout.decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        print(f"Error executing SQL: {e.stderr.decode('utf-8')}")
        sys.exit(1)

def run_pg_restore(db_kwargs, dump_path):
    """Restores a SQL dump file into the specified PostgreSQL database."""
    print(f"Restoring {dump_path} to database {db_kwargs['dbname']}...")
    env = os.environ.copy()
    if db_kwargs.get('password'):
        env['PGPASSWORD'] = db_kwargs['password']
        
    cmd = ['psql']
    if db_kwargs.get('host'):
        cmd.extend(['-h', db_kwargs['host']])
    if db_kwargs.get('port'):
        cmd.extend(['-p', str(db_kwargs['port'])])
    if db_kwargs.get('user'):
        cmd.extend(['-U', db_kwargs['user']])
        
    cmd.extend(['-d', db_kwargs['dbname'], '-f', dump_path])
    
    try:
        subprocess.run(cmd, env=env, check=True)
        print("Database restore completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error during restore: {e}")
        sys.exit(1)

from .queries import UNSUPPORTED_VIEW_MODES, UNSUPPORTED_MODULES, CUSTOM_CLEANUP_QUERIES, SECURITY_CLEANUP_QUERIES

def scrub_enterprise_artifacts(db_kwargs, reset_security=False):
    """Runs the SQL queries necessary to strip Enterprise components."""
    print("Scrubbing Enterprise artifacts from the database...")
    
    queries = [
        # 1. Mark Enterprise modules as uninstalled
        "UPDATE ir_module_module SET state = 'uninstalled' WHERE license = 'OEEL-1';"
    ]
    
    # Also uninstall any manually specified unsupported modules
    for module in UNSUPPORTED_MODULES:
        queries.append(f"UPDATE ir_module_module SET state = 'uninstalled' WHERE name = '{module}';")
        
    queries.extend([
        # 2. Deactivate views for uninstalled modules (fixes KanbanArchParser and Owl errors)
        "UPDATE ir_ui_view SET active = false WHERE id IN (SELECT res_id FROM ir_model_data WHERE model = 'ir.ui.view' AND module IN (SELECT name FROM ir_module_module WHERE state = 'uninstalled'));",
        
        # 3. Deactivate menus for uninstalled modules
        "UPDATE ir_ui_menu SET active = false WHERE id IN (SELECT res_id FROM ir_model_data WHERE model = 'ir.ui.menu' AND module IN (SELECT name FROM ir_module_module WHERE state = 'uninstalled'));",
    ])
    
    # 4. Clean up Enterprise view modes from window actions
    for view_mode in UNSUPPORTED_VIEW_MODES:
        queries.append(f"UPDATE ir_act_window SET view_mode = REPLACE(view_mode, ',{view_mode}', '') WHERE view_mode ILIKE '%{view_mode}%';")
        queries.append(f"UPDATE ir_act_window SET view_mode = REPLACE(view_mode, '{view_mode},', '') WHERE view_mode ILIKE '%{view_mode}%';")
        
    # 5. Delete specific view mode bindings that force Enterprise views
    modes_str = ", ".join(f"'{m}'" for m in UNSUPPORTED_VIEW_MODES)
    if modes_str:
        queries.append(f"DELETE FROM ir_act_window_view WHERE view_mode IN ({modes_str});")
        
    # 6. Run any custom cleanup queries provided by contributors
    queries.extend(CUSTOM_CLEANUP_QUERIES)

    # 7. Reset passwords and disable 2FA
    if reset_security:
        queries.extend(SECURITY_CLEANUP_QUERIES)
    
    for query in queries:
        run_psql_command(db_kwargs, query)
        
    print("Database scrubbing complete! Your database is ready for Odoo Community.")
    
    if reset_security:
        print("\n" + "="*50)
        print("SECURITY NOTICE:")
        print("All user passwords have been automatically reset to 'admin'!")
        print("Two-Factor Authentication (2FA) has also been disabled.")
        print("This ensures you won't be locked out of your local restored instance.")
        print("="*50 + "\n")
    
    print("IMPORTANT NEXT STEPS:")
    print("Run `odoo -u all -d <db_name>` to finalize the removal of uninstalled modules.")

def main():
    parser = argparse.ArgumentParser(description="Odoo Liberate: Migrate Enterprise backups to Community Edition.")
    parser.add_argument("zip_path", help="Path to the Odoo backup ZIP file.", nargs='?')
    
    # DB arguments
    parser.add_argument("-d", "--dbname", help="Target database name", required=True)
    parser.add_argument("-U", "--user", help="PostgreSQL user")
    parser.add_argument("-W", "--password", help="PostgreSQL password")
    parser.add_argument("-H", "--host", help="PostgreSQL host")
    parser.add_argument("-p", "--port", help="PostgreSQL port")
    
    # Filestore arguments
    parser.add_argument("--filestore-dest", help="Destination path to copy the filestore (e.g., /var/lib/odoo/filestore/db_name)")
    
    # Scrub only mode
    parser.add_argument("--scrub-only", action="store_true", help="Skip extraction and restore, only run the scrubbing SQL queries.")
    
    # Security options
    parser.add_argument("--reset-security", action="store_true", help="Automatically reset all user passwords to 'admin' and disable 2FA.")
    parser.add_argument("--security-only", action="store_true", help="Skip everything and ONLY run the security reset queries.")
    
    args = parser.parse_args()
    
    db_kwargs = {
        'dbname': args.dbname,
        'user': args.user,
        'password': args.password,
        'host': args.host,
        'port': args.port
    }
    
    if args.security_only:
        print("Running security reset only...")
        for query in SECURITY_CLEANUP_QUERIES:
            run_psql_command(db_kwargs, query)
        print("\n" + "="*50)
        print("SECURITY NOTICE:")
        print("All user passwords have been automatically reset to 'admin'!")
        print("Two-Factor Authentication (2FA) has also been disabled.")
        print("="*50 + "\n")
        sys.exit(0)
    
    if args.scrub_only:
        scrub_enterprise_artifacts(db_kwargs, reset_security=args.reset_security)
        sys.exit(0)
        
    if not args.zip_path:
        print("Error: zip_path is required unless --scrub-only or --security-only is specified.")
        parser.print_help()
        sys.exit(1)
        
    if not os.path.exists(args.zip_path):
        print(f"Error: File {args.zip_path} does not exist.")
        sys.exit(1)
        
    print(f"Extracting {args.zip_path}...")
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            with zipfile.ZipFile(args.zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
        except zipfile.BadZipFile:
            print("Error: Invalid zip file.")
            sys.exit(1)
            
        dump_path = os.path.join(tmpdirname, 'dump.sql')
        filestore_src = os.path.join(tmpdirname, 'filestore')
        
        if not os.path.exists(dump_path):
            print("Error: dump.sql not found inside the zip archive.")
            sys.exit(1)
            
        # 1. Restore Database
        run_pg_restore(db_kwargs, dump_path)
        
        # 2. Copy Filestore
        if args.filestore_dest:
            if os.path.exists(filestore_src):
                print(f"Copying filestore to {args.filestore_dest}...")
                os.makedirs(args.filestore_dest, exist_ok=True)
                shutil.copytree(filestore_src, args.filestore_dest, dirs_exist_ok=True)
                print("Filestore copy completed.")
            else:
                print("Warning: No 'filestore' directory found in the backup zip.")
                
        # 3. Scrub Enterprise Artifacts
        scrub_enterprise_artifacts(db_kwargs, reset_security=args.reset_security)

if __name__ == "__main__":
    main()

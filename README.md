# Odoo Liberate

A zero-dependency CLI tool to migrate Odoo Enterprise databases to Community Edition.

## Why this exists

When you restore an Odoo Enterprise backup on an Odoo Community instance, the database retains proprietary artifacts (like Enterprise-exclusive views, menus, modules, and `grid`/`gantt` view modes). Because the Community Edition doesn't have the source code to render these, the Odoo web client crashes with `OwlError` and `KanbanArchParser` tracebacks when you navigate the UI.

`odoo-liberate` automates the process of extracting the backup, restoring the database, copying the filestore, and most importantly, scrubbing these Enterprise artifacts directly from the database using SQL queries, so your instance can boot properly on Community Edition.

## Requirements
- Python 3.7+
- `psql` available in your system's PATH

## Installation

You can install `odoo-liberate` directly using `pip`:

```bash
pip install .
```

## Usage

### Full Migration (Extract, Restore, Scrub)

Run the tool against your `.zip` backup file generated from the Odoo database manager:

```bash
odoo-liberate backup.zip -d my_database -U my_db_user -W my_password --filestore-dest /var/lib/odoo/filestore/my_database
```

This will:
1. Extract `backup.zip` to a temporary directory.
2. Restore `dump.sql` into the `my_database` PostgreSQL database.
3. Copy the `filestore/` directory to `/var/lib/odoo/filestore/my_database`.
4. Run the scrubbing queries against `my_database`.

### Scrub Only (For an already restored database)

If you've already manually restored your database and just need to scrub the Enterprise artifacts to fix the UI crashes:

```bash
odoo-liberate -d my_database -U my_db_user -W my_password --scrub-only
```

### Important Next Step

After `odoo-liberate` finishes, you **MUST** run the following command to have Odoo's ORM finalize the removal of the deactivated Enterprise modules:

```bash
odoo -u all -d my_database
```

Once this is complete, restart your Odoo server and you're good to go!

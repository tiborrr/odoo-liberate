# Odoo Liberate

A zero-dependency CLI tool to migrate Odoo Enterprise databases to Community Edition.

## Why this exists

When you restore an Odoo Enterprise backup on an Odoo Community instance, the database retains proprietary artifacts (like Enterprise-exclusive views, menus, modules, and `grid`/`gantt` view modes). Because the Community Edition doesn't have the source code to render these, the Odoo web client crashes with `OwlError` and `KanbanArchParser` tracebacks when you navigate the UI.

`odoo-liberate` automates the process of extracting the backup, restoring the database, copying the filestore, and most importantly, scrubbing these Enterprise artifacts directly from the database using SQL queries, so your instance can boot properly on Community Edition.

## Requirements
- Python 3.7+
- `psql` available in your system's PATH

## Installation

You can run `odoo-liberate` directly using `uv`:

```bash
uv tool install .
```
Or run it without installing using:
```bash
uv run odoo-liberate
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

## Troubleshooting & Common Pitfalls

When restoring cloud backups locally, you might run into a few common gotchas that this tool cannot automatically fix for you. Here is how to resolve them:

### 1. "Too many login failures" (Rate Limiting)
If you try to log into the restored database with the wrong password too many times, Odoo will lock you out. Since it's a restored database, your local `.env` default passwords (like `admin`) might not work.
**Fix**: Simply restart your Odoo web container/server. The rate-limit cache is cleared on restart, allowing you to try again.

### 2. Two-Factor Authentication (2FA) Lockout
If the admin account had 2FA enabled on the cloud environment, you won't be able to log in locally without the authenticator app.
**Fix**: You can force-disable 2FA for your user directly in PostgreSQL by removing their TOTP secret:
```sql
UPDATE res_users SET totp_secret = NULL WHERE login = 'your_email@example.com';
```

### 3. Forgotten Passwords
Because the restored database contains the hashed passwords from your cloud environment, you must use your cloud password. If you don't remember it, you can forcefully reset the password to something simple (like `admin`) via the Odoo shell:
```bash
echo "env['res.users'].search([('login', '=', 'your_email@example.com')]).write({'password': 'admin'})
env.cr.commit()" | odoo shell -d my_database
```

### 4. `psql` Restoration Errors (`relation does not exist`)
When `odoo-liberate` restores the `dump.sql`, you might see some `ERROR:` messages in the console (e.g., `relation "public.ai_embedding" does not exist` or `role "odoo" does not exist`).
**Fix**: This is entirely normal! Odoo Cloud environments often use proprietary PostgreSQL extensions (like `pgvector`) or specific roles that your local standard Postgres image lacks. `odoo-liberate` intentionally runs the restore command in a way that ignores these missing relations and continues restoring all the standard tables. You can safely ignore these errors.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for a guide on how to add new modules, view modes, or custom SQL queries to make the database scrubbing process even more robust.

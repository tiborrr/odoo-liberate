# Contributing to Odoo Liberate

We welcome contributions to make `odoo-liberate` more robust! As Odoo updates its Enterprise modules, new proprietary views, modules, or artifacts might break the Community Edition.

If you encounter an `OwlError`, `KanbanArchParser` error, or any other traceback indicating a missing view mode or module when migrating a database, you can easily add rules to scrub those artifacts.

## How to Extend the Cleaning Process

All of the customizable configurations are located in `src/odoo_liberate/queries.py`. 

### 1. Unsupported View Modes

If a new Enterprise view mode (e.g., `grid`, `gantt`) is causing crashes:
Add the view mode string to the `UNSUPPORTED_VIEW_MODES` list in `queries.py`.
```python
UNSUPPORTED_VIEW_MODES = [
    "grid",
    "gantt",
    "cohort",
    "map",
    # Add your new view mode here
]
```
The script will automatically strip this mode from all window actions and delete associated view bindings.

### 2. Unsupported Modules

By default, the script uninstalls ALL modules that have `license = 'OEEL-1'`. However, some custom or obscure modules might slip through.
Add the module's technical name to the `UNSUPPORTED_MODULES` list:
```python
UNSUPPORTED_MODULES = [
    "studio_customization",
    # Add your module name here
]
```

### 3. Custom SQL Cleanup Queries

If your migration requires a highly specific SQL query to clean up a custom table or orphaned record, add it to `CUSTOM_CLEANUP_QUERIES`:
```python
CUSTOM_CLEANUP_QUERIES = [
    "DELETE FROM ir_actions_server WHERE state = 'code' AND name ILIKE '%enterprise%';",
    # Add your SQL query here
]
```

## Submitting your changes

1. Fork the repository
2. Edit `src/odoo_liberate/queries.py`
3. Test your changes locally against a database backup
4. Submit a Pull Request explaining what module/view mode you added and what error it resolves

Thank you for helping liberate Odoo databases!

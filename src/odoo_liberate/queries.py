"""
Configuration file for Odoo Liberate.

This file makes it easy to add new Enterprise modules, view modes, or custom SQL queries 
to ensure they are cleaned up during the migration process. Contributions are welcome!
"""

# Add any Enterprise-exclusive view modes here.
# These will be stripped from window actions and deleted from view bindings.
UNSUPPORTED_VIEW_MODES = [
    "grid",
    "gantt",
    "cohort",
    "map",
]

# Add any specific Enterprise modules that must be uninstalled here.
# By default, odoo-liberate automatically uninstalls ALL modules with license = 'OEEL-1'.
# If you find a module that breaks Community Edition but isn't caught by the license check, add it here.
UNSUPPORTED_MODULES = [
    # e.g., 'studio_customization',
]

# Add any raw SQL queries here that need to be executed during the scrub phase.
# These will run after the modules and views are deactivated.
CUSTOM_CLEANUP_QUERIES = [
    # e.g., "DELETE FROM ir_actions_server WHERE state = 'code' AND name ILIKE '%enterprise%';"
]

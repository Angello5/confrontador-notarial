from django.contrib.admin.apps import AdminConfig


class ERPAdminConfig(AdminConfig):
    default_site = "accounts.admin_site.ERPAdminSite"

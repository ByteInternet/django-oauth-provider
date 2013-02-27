from oauth_provider.compat import url, patterns, include

from django.contrib import admin

from oauth_provider.views import protected_resource_example

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^oauth/', include('oauth_provider.urls')),
    url(r'^oauth/photo/$', protected_resource_example, name='oauth_example'),
    url(r'^admin/', include(admin.site.urls)),
)

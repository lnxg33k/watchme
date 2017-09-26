from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from APIs import views

urlpatterns = [
    url(r'^$', views.api_root),
    url(r'^hits/$', views.HitList.as_view(), name='hits'),
    url(r'^hits/(?P<pk>[0-9]+)/$', views.HitDetail.as_view()),

    url(r'^watchers/$', views.WatcherConfigList.as_view(), name='watchers'),
    url(r'^watchers/(?P<pk>[0-9]+)/$', views.WatcherConfigDetail.as_view()),

    url(r'^tag-autocomplete/$',
        views.TagAutocomplete.as_view(), name='tag-autocomplete'),

    # url(r'^errors/$', views.ErrorList.as_view(), name='errors'),
    # url(r'^errors/(?P<pk>[0-9]+)/$', views.ErrorDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)

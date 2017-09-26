from APIs.models import Hit, WatcherConfig, Tag
from APIs.serializers import (
    HitSerializer, WatcherConfigSerializer)

from rest_framework import generics
from rest_framework import filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from dal import autocomplete


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'Hits': reverse('hits', request=request, format=format),
        'Watchers': reverse('watchers', request=request, format=format),
    })


class HitList(generics.ListCreateAPIView):
    queryset = Hit.objects.all()
    serializer_class = HitSerializer
    filter_fields = ('is_malicious', 'md5sum', 'sha256sum', 'fileExtension', )
    search_fields = ('src_path', 'fileType')


class HitDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Hit.objects.all()
    serializer_class = HitSerializer


class WatcherConfigList(generics.ListCreateAPIView):
    queryset = WatcherConfig.objects.all()
    serializer_class = WatcherConfigSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=server_name',)


class WatcherConfigDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = WatcherConfig.objects.all()
    serializer_class = WatcherConfigSerializer


class TagAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        # if not self.request.user.is_authenticated():
        #     return Tag.objects.none()

        qs = Tag.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

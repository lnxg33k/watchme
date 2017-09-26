from rest_framework import serializers
from APIs.models import Hit, WatcherConfig  # , Error


class HitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hit
        fields = "__all__"
        depth = 1


class WatcherConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatcherConfig
        fields = "__all__"


# class ErrorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Error
#         fields = ('id', 'traceback')

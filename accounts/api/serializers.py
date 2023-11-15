from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from accounts.models import Profile
from django.contrib.auth import get_user_model
User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        depth = 1


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = "__all__"

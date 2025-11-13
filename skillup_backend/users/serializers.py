from rest_framework import serializers
from django.contrib.auth import get_user_model
from goals.serializers import UserBadgeSerializer

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,style={"input_type":"password"})
    password2=serializers.CharField(write_only=True,style={"input_type":"password"})
    first_name=serializers.CharField(max_length=30)
    last_name=serializers.CharField(max_length=68)
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)  # declare file field
    bio = serializers.CharField(required=False, allow_blank=True, write_only=True)  # optional text field

    class Meta:
        model = User
        fields = ('username', 'email','first_name','last_name','password','password2', 'avatar', 'bio')


    def validate(self, attrs):
        password=attrs.get('password')
        password2=attrs.get('password2')
        if password!=password2:
            raise serializers.ValidationError("Password and Confirm password doesn't match")
        return attrs

    def create(self, validated_data):
        # Remove password2 because not used for user creation
        password2 = validated_data.pop('password2', None)
        avatar = validated_data.pop('avatar', None)
        bio = validated_data.pop('bio', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )
        if avatar is not None:
            user.avatar = avatar
        user.bio = bio
        user.save()
        return user
class UserSerializer(serializers.ModelSerializer):
    badges = UserBadgeSerializer(source='user_badges', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'xp_points', 'level', 'streak_count', 'avatar', 'bio','badges')

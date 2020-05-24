from django.contrib import admin
from forum.models import PostCategory,PostIcon,UserDetails,Thread,Comment
# Register your models here.
admin.site.register(PostCategory)
admin.site.register(PostIcon)
admin.site.register(UserDetails)
admin.site.register(Thread)
admin.site.register(Comment)
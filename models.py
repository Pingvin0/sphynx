from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse

User = get_user_model()
# Create your models here.

class PostCategory(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name

    def getRecentThreads(self, ammount=20):
        return self.thread_set.all().order_by("-posted")[:ammount]

class PostIcon(models.Model):
    path = models.CharField(max_length=150)
    
    def __str__(self):
        return self.path


class UserDetails(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    custom_title = models.CharField(max_length=30, null=True)
    profile_pic = models.CharField(max_length=30, default="new.png")
    bio = models.CharField(max_length=150, blank=True)
    moderator = models.BooleanField(default=False)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserDetails.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userdetails.save()



class Thread(models.Model):
    title = models.CharField(max_length=25)
    category = models.ForeignKey(PostCategory, on_delete=models.CASCADE)
    icon = models.IntegerField()
    body = models.TextField(max_length=500)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE) # TODO: no cascade, just write banned user
    posted = models.DateTimeField(default=timezone.now)
    edited_on = models.DateTimeField(null=True)

    def __str__(self):
        return self.title

    def getRedirect(self):
        return HttpResponseRedirect(reverse('sphynx:thread', kwargs={'id': self.id}))

    def hasPermissionToEdit(self, user):
        if user.is_authenticated == False:
            return False
        if self.author == user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        if user.userdetails.moderator:
            return True
        return False
        


class Comment(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    body = models.TextField(max_length=500) # TODO: max length to settings
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    posted = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.body


#TODO: add bookmark

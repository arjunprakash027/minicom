from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    participant_email = models.CharField(max_length=255, db_index=True)
    sender_type = models.CharField(max_length=5, choices=[('admin','Admin'),('user','User')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}"
    

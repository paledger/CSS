from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.conf import settings
import MySQLdb
import re
from django.db import IntegrityError

# ---------- User Models ----------
class CUserManager(models.Manager):
    # Verify email is valid
    def is_valid_email(self, email): 
        #@ TODO FIX REGEX
        #if re.match(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', email) is None:
        #    raise ValueError("Attempted CUser creation"+ 
        #                     "with invalid email address")
        return email

    # @TODO Come up with password patten and validate it here
    def is_valid_password(self, password):
        if password is '':
            raise ValueError("Attempted CUser creation with invalid password")
        return password

    # Verify user_type is either 'scheduler' or 'faculty'
    def is_valid_user_type(self, user_type):
        if user_type != 'scheduler' and user_type != 'faculty':
            raise ValueError("Attempted CUser creation with invalid user_type")
        return user_type

    def create_cuser(self, email, password, user_type):
        try:
            user = self.create(user=User.objects.create_user(
                                   username=self.is_valid_email(email), 
                                   email=self.is_valid_email(email),
                                   password=self.is_valid_password(password)),
                               user_type=self.is_valid_user_type(user_type))
        except IntegrityError as e:
            raise ValueError("Trying to add duplicate faculty")
        return user

    def get_faculty(self):
        return self.filter(user_type='faculty')

    def get_scheduler(self):
        return self.filter(user_type='faculty')

class CUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    user_type = models.CharField(max_length=16)

    objects = CUserManager()
 
class FacultyDetails(models.Model):
    # The user_id uses the User ID as a primary key.
    # Whenever this User is deleted, this entry in the table will also be deleted
    user = models.OneToOneField(CUser, on_delete=models.CASCADE, blank=False)
    target_workload = models.IntegerField() # in hours
    changed_preferences = models.CharField(max_length=1) # 'y' or 'n' 

# ---------- Resource Models ----------
# Room represents department rooms
class Room(models.Model):
   name = models.CharField(max_length=32)
   description = models.CharField(max_length=256, null=True)
   capacity = models.IntegerField(default=0)
   notes = models.CharField(max_length=1024, null=True)
   equipment = models.CharField(max_length=1024, null=True)

   def validate_name(name):
      if name.length > 32:
         raise ValidationError("Room name is longer than 32 characters")

   def validate_description(description):
      if description.length > 256:
         raise ValidationError("Room description is longer than 256 characters")
   
   def validate_notes(notes):
      if notes.length > 1024:
         raise ValidationError("Room notes is longer than 1024 characters")
   
   def validate_description(description):
      if description.length > 256:
         raise ValidationError("Room description is longer than 256 characters")



# Course represents a department course offering
class Course(models.Model):
    course_name = models.CharField(max_length=16)
    equipment_req = models.CharField(max_length=2048, null=True)
    description = models.CharField(max_length=2048, null=True)

    def get_name(self):
    	return self.course_name

    def get_equipment_req(self):
    	return self.equipment_req

    def get_description(self):
    	return self.description

# SectionType contains all the defined section types the department allows
class SectionType(models.Model):
    section_type = models.CharField(max_length=32, primary_key=True) # eg. lecture or lab


# WorkInfo contains the user defined information for specific Course-SectionType pairs
# Each pair has an associated work units and work hours defined by the department
class WorkInfo(models.Model): 
    class Meta:
        unique_together = (("course", "section_type"),)
    course = models.ForeignKey(Course, on_delete = models.CASCADE)
    section_type = models.ForeignKey(SectionType, on_delete = models.CASCADE)
    work_units = models.IntegerField(default = 0)
    work_hours = models.IntegerField(default = 0)

class Availability(models.Model):
    class Meta: 
        unique_together = (("faculty_id", "days_of_week", "start_time"),)
    faculty_id = models.OneToOneField(Faculty, on_delete=models.CASCADE) #
    days_of_week = models.CharField(max_length=16) # MWF or TR
    start_time = models.TimeField()
    end_time = models.TimeField()
    level = CharField(16) # unavailable, preferred, unavailable

    

# ---------- Scheduling Models ----------
# Schedule is a container for scheduled sections and correponds to exactly 1 academic term
class Schedule(models.Model):
    academic_term = models.CharField(max_length=16, unique=True) # eg. "Fall 2016"
    state = models.CharField(max_length=16, default="active") # eg. active or finalized 

    def finalize_schedule(self):
    	self.state = "finalized"

    def return_to_active(self):
    	self.state = "active"

# Section is our systems primary scheduled object
# Each section represents a department section that is planned for a particular schedule
class Section(models.Model):
    schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE, unique=True)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    days = models.CharField(max_length = 8)    # MWF or TR
    faculty = models.ForeignKey(CUser, null = True, on_delete = models.SET_NULL, default = models.SET_NULL)
    room = models.OneToOneField(Room, null = True, on_delete = models.SET_NULL, default = models.SET_NULL)
    section_capacity = models.IntegerField(default = 0)
    students_enrolled = models.IntegerField(default = 0)
    students_waitlisted = models.IntegerField(default = 0)
    conflict = models.CharField(max_length = 1)  # y or n
    conflict_reason = models.CharField(max_length = 8) # faculty or room
    fault = models.CharField(max_length = 1) # y or n
    fault_reason = models.CharField(max_length = 8) # faculty or room
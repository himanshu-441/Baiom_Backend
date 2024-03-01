from django.db import models
from django.utils import timezone
from course.models import Course, Batch
import datetime
from userauths.models import Dashboard_User

# Create your models here.
####################### SUBSCRIPTION PLANS ################# 

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    price = models.FloatField()
    discount = models.FloatField(default=0)  # Add discount field
    months = models.PositiveIntegerField()

    @property
    def total_amount_after_discount(self):
        # Calculate total amount after applying discount
        return self.price * (1 - self.discount / 100)

    def __str__(self):
        return f"{self.name} - {self.total_amount_after_discount}"


class SubscriptionPlanCourse(models.Model):
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, blank=True,null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    included_in_plan = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    available_slots = models.IntegerField(default=-1)  # -1 for unlimited

    def __str__(self):
        return f"{self.subscription_plan.name} - {self.course.title}"

    def is_active(self):
        if self.start_date and self.end_date:
            return self.active and self.start_date <= timezone.now().date() <= self.end_date
        return self.active

    def is_available(self):
        if self.available_slots == -1:
            return True
        subscribed_count = Purchase.objects.filter(course=self.course, subscription_plan=self.subscription_plan).count()
        return subscribed_count < self.available_slots

    def save(self, *args, **kwargs):
        if self.start_date and self.subscription_plan.months:
            # Calculate end date based on start date and months
            end_date = self.start_date + datetime.timedelta(days=30 * self.subscription_plan.months)
            self.end_date = end_date
        super().save(*args, **kwargs)
        
        
class PurchaseCourse(models.Model):
    dashboard_user = models.ForeignKey(Dashboard_User, on_delete=models.CASCADE, null=True, blank=True)
    purchased_course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE,blank=True, null=True)
    Batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    purchase_date = models.DateField(auto_now_add=True)
    plans_duration_months = models.PositiveIntegerField(editable=False)
    purchase_start_date = models.DateField()
    purchase_end_date = models.DateField()
    additional_access_date = models.DateField()

    
    def __str__(self):
        return f"{self.purchased_course.title} - {self.subscription_plan.name} - {self.dashboard_user.fname}"

    def is_course_access_valid(self):
        now = timezone.now()
        return self.purchase_start_date <= now <= self.purchase_end_date

    def can_access_recorded_videos(self):
        now = timezone.now()
        return self.purchase_end_date <= now <= self.additional_access_date

    def save(self, *args, **kwargs):
        # Calculate plans_duration_months based on the subscription plan
        if self.subscription_plan:
            self.plans_duration_months = self.subscription_plan.months
            # Calculate purchase_end_date based on purchase_start_date and plans_duration_months
            self.purchase_end_date = self.purchase_start_date + datetime.timedelta(days=30 * self.plans_duration_months)
        super().save(*args, **kwargs)
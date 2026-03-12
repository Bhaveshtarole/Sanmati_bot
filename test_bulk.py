import os
import sys
from app.routers.dashboard import _drip_broadcast

file_path = "uploads/test_broadcast.csv"
template_name = "hello_world"
batch_size = 50
delay_minutes = 0

print("Starting test broadcast...")
_drip_broadcast(file_path, template_name, batch_size, delay_minutes)
print("Test broadcast script finished.")

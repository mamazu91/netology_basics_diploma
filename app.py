from photobackup import VkPhotoBackup

vk_owner_id = input('Please enter VK profile ID: ')
vk_access_token = input('Please enter Yandex Disk access token: ')

backup = VkPhotoBackup(vk_owner_id, vk_access_token)
print(backup.upload_photos())

from photobackup import VkPhotoBackup

photos_owner_id = input('Please enter VK profile ID: ')
vk_access_token = input('Please enter VK access token: ')
ya_access_token = input('Please enter Yandex Disk access token: ')

backup = VkPhotoBackup(photos_owner_id, vk_access_token, ya_access_token)
print(backup.upload_photos())

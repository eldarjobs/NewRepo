from InquirerPy import inquirer
from source.telegram.Telegram import Telegram
from source.model.Credentials import Credentials
from source.model.ForwardConfig import ForwardConfig
from source.utils.Console import Terminal
from PIL import Image, ImageDraw, ImageFont
import os
import io  # For handling images in memory


class Bot:
    def __init__(self):
        self.telegram = Telegram(Credentials.get(True))

    options = [
        {"name": "Add/Update Credentials", "value": "1"},
        {"name": "List Chats", "value": "2"},
        {"name": "Forward Messages", "value": "3"},
        {"name": "Add Watermark to Photos", "value": "4"},
        {"name": "Exit", "value": "0"}
    ]
    console = Terminal.console

    async def start(self):
        try:
            while True:
                choice = await inquirer.select(
                    message="Menu:",
                    choices=Bot.options).execute_async()
                if choice == "0":
                    Terminal.console.print("[bold red]Exiting...[/bold red]")
                    break
                elif choice == "1":
                    await self.update_credentials()
                elif choice == "2":
                    await self.list_chats()
                elif choice == "3":
                    await self.start_forward()
                elif choice == "4":
                    await self.add_watermark()  # Call the method here
                else:
                    self.console.print("[bold red]Invalid choice[/bold red]")
        except Exception as err:
            raise err
        finally:
            self.telegram.client.disconnect()

    async def update_credentials(self):
        self.console.clear()
        self.telegram.client.disconnect()
        self.telegram = Telegram(Credentials.get(False))

    async def list_chats(self):
        self.console.clear()
        await self.telegram.list_chats()

    async def start_forward(self):
        forward_config_list = await ForwardConfig.get_all(True)
        forwardConfigString = '\n   '.join(str(forwardConfig) for forwardConfig in forward_config_list)
        forward_options = [
            {
                "name": "Use saved settings.\n   " + forwardConfigString,
                "value": "1"
            },
            {
                "name": "New settings",
                "value": "2"
            }
        ]

        forward_choice = await inquirer.select(
            message="Forward Settings:",
            choices=forward_options
        ).execute_async()

        if forward_choice == "2":
            forward_config_list = await ForwardConfig.get_all(False)
        forward_config_map = {item.sourceID: item for item in forward_config_list}

        forward_type = [
            {
                "name": "Live",
                "value": "1"
            },
            {
                "name": "Past",
                "value": "2"
            }
        ]

        type_choice = await inquirer.select(
            message="Forward Type:",
            choices=forward_type
        ).execute_async()


        if type_choice == "1":
            for source_id, config in forward_config_map.items():  # This assumes forward_config_map is a dictionary
                photos = await self.telegram.get_photos(source_id)
                for photo in photos:
                    # Download the photo to a local path
                    photo_path = await self.telegram.client.download_media(photo, file="downloads/")
                    
                    # Add watermark to the photo
                    watermarked_photo_path = await add_watermark(photo_path, "Custom Watermark")
                    
                    if watermarked_photo_path:
                        # Use the ForwardConfig to forward the watermarked photo
                        await self.telegram.send_photo(config.destinationID, watermarked_photo_path)



        else:
            await self.telegram.past(forward_config_map)


async def add_watermark(photo_path, watermark_text):
    try:
        # Open the image
        image = Image.open(photo_path)
        draw = ImageDraw.Draw(image)

        # Load the font
        font = ImageFont.truetype("arial.ttf", 36)

        # Calculate text position (bottom-right corner)
        # Using textbbox instead of the deprecated textsize
        bbox = draw.textbbox((0, 0), watermark_text, font=font)  # Get the bounding box of the text
        text_width = bbox[2] - bbox[0]  # width = x2 - x1
        text_height = bbox[3] - bbox[1]  # height = y2 - y1
        position = (image.width - text_width - 10, image.height - text_height - 10)

        # Add the watermark text
        draw.text(position, watermark_text, fill=(255, 255, 255), font=font)

        # Save the watermarked image
        watermarked_photo_path = "watermarked_" + os.path.basename(photo_path)  # Ensure the filename is correct
        image.save(watermarked_photo_path)

        return watermarked_photo_path

    except Exception as e:
        print(f"Error while adding watermark: {e}")
        return None


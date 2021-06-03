# wellbeing chatbot

## Requirements

- Docker
- Ngrok
- Python < 3.9
- Rasa == 2.5.0 (only required for training the model)

### Build
To build the image:
```
docker build . -t <name_of_the_image>:v<number>
```
Then, edit image slot under app in docker-compose file to run this image

### Local mode

To run the model in local mode run:

```
docker-compose up
ngrok http 5005
```

import pika
import time

from doravoc.video_extractor import extract_videos
from doravoc.video_objclass import recognize_video_objects


def update_status_file(new_status: str, request_id: str) -> None:
    with open(f'media/{request_id}_status.txt', 'w') as sf:
        sf.write(new_status)


# Process
def process_request(request_id: str) -> None:
    try:
        update_status_file('Extracting source RGB and DEPTH videos', request_id=request_id)
        extract_videos(request_id=request_id)
        update_status_file('Recognizing objects', request_id=request_id)
        recognize_video_objects(request_id)
        update_status_file('Finished', request_id=request_id)
    except Exception:
        update_status_file(f'Error', request_id=request_id)


# Callback function
def on_request(ch, method, props, body):
    """Module request callback function"""
    request_id = body.decode()
    print(f'[INFO] Recieved request #{request_id}.')
    ch.basic_ack(delivery_tag=method.delivery_tag)
    try:
        process_request(request_id=request_id)
        print(f'[INFO] Request #{request_id} is done!')
    except Exception as error:
        print(f'[ERROR] Request #{request_id} failed: {error}')


# ML module entrypoint
if __name__ == '__main__':
    print('[INFO] Delay before connecting to RabbitMQ...')
    time.sleep(10)

    # Estabilishing AMQP connection to RabbitMQ container
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))

    channel = connection.channel()
    channel.queue_declare(queue='tasks', durable=True)

    # Listen to tasks queue
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='tasks', on_message_callback=on_request)

    print("[INFO] Waiting for tasks.")
    channel.start_consuming()
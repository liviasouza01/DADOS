from quixstreams import Application 
import os

app = Application(
    broker_address=os.environ.get("KAFKA_BROKER_ADDRESS", "localhost:19092"),
    consumer_group="json__trade_to_ohlc_consumer_group",
)

input_topic = app.topic('trades', value_deserializer='json')
output_topic = app.topic('ohlc_features', value_serializer='json')

sdf = app.dataframe(input_topic)

#10s window aggregations
sdf = sdf.tumbling_window(timedelta(seconds=WINDOW_SECONDS), 0) \
    .reduce(reduce_price, init_reduce_price) \
    .final()    

sdf = sdf.to_topic(output_topic)

app.run(sdf)
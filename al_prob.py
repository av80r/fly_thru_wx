from pyspark import SparkContext
from pyspark.sql import SQLContext
import mbd_util as u


sc = SparkContext(appName="wx_prob")
sc.setLogLevel('ERROR')
sqlContext = SQLContext(sc)

def reduce_airlines(agg, new_value):
	for k, v in new_value.items():
		if k in agg:
			agg[k] += v
		else:
			agg[k] = v
	return agg
	
def al_probs(b, d):
	# Gets a dictionary with AL Op names per block as d
	# Returns list of tuples key, value where key is a tuple block_name, Op string and value is prob
	output = []
	b_lat, b_lon = b
	ac_in_b = 0.0
	for k, v in d.items():
		ac_in_b += v	
	for k, v in d.items():
		output.append( (((b_lat, b_lon), k), v/ac_in_b) )
	return output

df = sqlContext.read.json("file:///home/s1638696/flight_data/2017-12-19-small.tar.gz")
#df = sqlContext.read.json("hdfs:///user/s1638696/flight_data/*")
airlines_per_block = df.rdd.filter(lambda r: not (r.Lat is None or r.Long is None or r.Op is None)).map(lambda r: (u.block_name(r.Lat, r.Long), {r.Op: 1}))
# This should be aggregate by key. Aggregate operates on partitions instead of combining values accross partitions
red_al = airlines_per_block.reduceByKey(reduce_airlines)
al_prob = red_al.flatMap(lambda (b, d): al_probs(b,d)) 

al_prob.toDF().write.json("file:///home/s1542648/al_prob.json", mode="overwrite")
#al_prob.toDF().write.json("/user/s1638696/ac_output/al_prob.json", mode="overwrite")
All query-day pairs prediction results (using raw ndcg@10 for each day):

|                      |  mb2011&2012                | mb2015&rts2016              | rts2017 |
| -------------------- |:---------------------------:| ---------------------------:| -------:|
| QPPd                 | 0.3279<sup>*b*</sup>        | 0.2712                      | 0.3301  |
| QPPm                 | 0.3462<sup>*bdca*</sup>     | **0.2848**<sup>*bdca*</sup> | 0.3136<sup>mca</sup>  |
| QPPc                 | 0.3315<sup>*b*</sup>       | 0.2716                       | 0.3222  |
| QPPc + TR            | 0.3306<sup>*b*</sup>       | 0.2716                       | 0.3222  |
| TR                   | **0.3471**<sup>*bdca*</sup> | 0.2839<sup>*bdca*</sup>     | **0.3343**<sup>*mca*</sup> |
| per-topic-day-oracle | 0.3653                      | 0.3462                      | 0.4037                     |
| best_baseline        | 0.2960                      | 0.2599                      | 0.3252                     |

Note that *d*, *m*, *c*, *a*, *b*, *t* indicate the effectiveness is statistically significantly higher with **p < 0.01** against 
*QPPd*, *QPPm*, *QPPc*, *QPPc+TR*, *best_baseline*, *TR*


Non-silent query day pairs prediction results (using raw ndcg@10 for each day):

|                      |  mb2011&2012                | mb2015&rts2016              | rts2017 |
| -------------------- |:---------------------------:| ---------------------------:| -------:|
| QPPd                 | 0.4456<sup>*b*</sup>        | 0.3569                      | 0.4008<sup>mca</sup>  |
| QPPm                 | 0.4704<sup>*bdca*</sup>     | **0.3748**<sup>*bdca*</sup> | 0.3808  |
| QPPc                 | 0.4506<sup>*b*</sup>        | 0.3575                      | 0.3913  |
| QPPc + TR            | 0.4493<sup>*b*</sup>        | 0.3575                      | 0.3913  |
| TR                   | **0.4717**<sup>*bdca*</sup> | 0.3737<sup>*bdca*</sup>     | **0.4060**<sup>*mca*</sup> |
| per-topic-day-oracle | 0.4964                      | 0.4557                      | 0.4902                     |
| best_baseline        | 0.4022                      | 0.3421                      | 0.3950                    |

Note that *d*, *m*, *c*, *a*, *b*, *t* indicate the effectiveness is statistically significantly higher with **p < 0.01** against 
*QPPd*, *QPPm*, *QPPc*, *QPPc+TR*, *best_baseline*, *TR*

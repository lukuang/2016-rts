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
| QPPd                 | 0.3958<sup>*mt*</sup>       | 0.3227<sup>*mt*</sup>       | 0.3463<sup>*mb*</sup>  |
| QPPm                 | 0.3723                      | 0.3019                      | 0.3309  |
| QPPc                 | 0.3963<sup>*mt*</sup>       | 0.3232<sup>*mt*</sup>       | 0.3447<sup>*mb*</sup>  |
| QPPc + TR            | 0.3950<sup>*mt*</sup>       | 0.3212<sup>*mt*</sup>       | 0.3437<sup>*mb*</sup>  |
| TR                   | 0.3581                      | 0.2980                      | 0.3353  |
| per-topic-day-oracle | 0.4964                      | 0.4557                      | 0.4902  |
| cv_baseline          | 0.3974                      | 0.3249                      | 0.3295  |

Note that *d*, *m*, *c*, *a*, *b*, *t* indicate the effectiveness is statistically significantly higher with **p < 0.01** against 
*QPPd*, *QPPm*, *QPPc*, *QPPc+TR*, *best_baseline*, *TR*

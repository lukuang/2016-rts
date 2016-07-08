
#!/bin/sh
# Tell the SGE that this is an array job, with "tasks" to be numbered 1 to 10000
#$ -l standby=1,h_rt=4:00:00
#$ -l m_mem_free=1G
#$ -t 1-400
vpkg_require python
vpkg_require python-numpy
vpkg_require python-scipy
source /home/1546/myEV/bin/activate
# When a single command in the array job is sent to a compute node,
# its task number is stored in the variable SGE_TASK_ID,
# so we can use the value of that variable to get the results we want:
echo python /lustre/scratch/lukuang/2016-RTS/src/2016-rts/my_code/process_tweet/build_index_achive.py $dest 400 -i $method $SGE_TASK_ID
python /lustre/scratch/lukuang/2016-RTS/src/2016-rts/my_code/process_tweet/build_index_achive.py $dest  400 -i $method $SGE_TASK_ID

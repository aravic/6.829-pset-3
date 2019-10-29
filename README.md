
# Designing ABR Algorithms

## Introduction

After her successful stint at Massive Internet Transfers, Alyssa P. Hacker was hired as
CTO of Multinational Internet Television, a company that streams on-demand TV
shows to users. The company is facing a critical problem: users on cellular
connections have a terrible streaming experience: their video is either too low
quality or they rebuffer too often.
As her first hire, you've been tasked with implementing an ABR scheme to
maximize the Quality of Experience for users on cellular connections.

For this part of the assignment, you will be writing ABR (adaptive bitrate) algorithms.
We've provided you with an ABR environment that can deterministically simulate a
video player and report the QoE values achieved by your ABR algorithm.
Using simulation instead of using a real testbed has the following major advantages:

 - *Determinism*: Every run is deterministic. There can be no noise introduced by
 various platforms into the components of an ABR system (e.g. network, browser,
 video player). We have noticed from the previous psets that mahimahi
 and VirtualBox when run together can behave poorly.
 CCP on cellular traces leads to random kernel crashes sometimes.
 This time since everything is done in simulation you don't have to worry about
 any of theses issues happening. All the code runs in python which is far
 easier to debug and script than other third-party closed applications.
 - *Speed*: Simulation for ABR is atleast a couple of orders of magnitude faster
  than performing the experiments on a realistic setup. This is a major benefit,
 especially if you would quickly like to evaluate an algorithm on multiple set of traces.
 This speed also lets us evaluate your algorithm on a wide variety of traces
 reducing the noise and variance on the leaderboard.
 - *Ease of installation*: All you have to install is python and few standard
 widely used python modules (no mahimahi, no ccp, no chrome-browser,
 no dash client, no rust; just python.). We have given you a script to automate
 the installation process.

**Please make sure to review the honor code at the end of this page before you even start
attempting this pset.**
### System description
In a realistic ABR setting, a client (typically a mobile device) is streaming video from a web server on a
bandwidth-limited network link (typically a cellular link). The ABR algorithm runs on the client end and
predicts decisions about the next bitrate to fetch based on the network conditions and current client state.
Client state includes features such as its current buffer occupancy among others. These decisions made by
the ABR algorithm affect the QoE experienced by the user(s) watching the video. For instance, if the ABR
algorithm always fetches video chunks of low quality, then it might never lead to buffering but it would lead to
poor perceptual video quality. On the other hand, if it always fetches chunks of the highest quality, then it
might encounter severe levels of buffering when the network bandwidth is low. So, a good ABR algorithm
has to *adapt* to the current network conditions.

In this pset, we ask you to implement a simple function that takes as input the video metadata,
qoe objective function and information about the encountered network conditions to predict the
a bitrate to fetch for the next chunk.

We provide code to simulate the cellular variable network conditions, video playback logic and other components
to evaluate your abr algorithm.

## Setup
### Installation

This repo provides a Vagrantfile that you can use to setup the VM in virtualbox. Note that although we've encountered some
issues with virtualbox in the past psets, these issues will not recur this time since we've moved completely to simulation.
It should be straightforward to use EC2 as well if you wish. We've tested that the starter code works correctly with vagrant. We haven't done so on EC2 but we expect it to be quite straightforward.
We provide the setup instructions for vagrant below. These should be fairly similar to EC2 as well.
#### vagrant
On your host machine, from the starter repo, do the following

 - `vagrant up`
 - ssh into the VM using `vagrant ssh`
- Run the following command from the VM after ssh login: ```sudo apt-get update && sudo apt-get upgrade -y```
  - If you see any errors, then restart the VM and try again. You would have to run `vagrant halt` and `vagrant up` on the host machine from the starter repo directory in order to restart.
- After the above step is successful, you should be able to see files present in `/abr` directory. If not `vagrant up` command did not execute correctly. Restart the VM and try again.
- Now run the following: `cd /abr` and `sudo ./install.sh`
  - This should do the following:
    - Install python and required python packages
    - Download the traces from our leaderboard server.
    - If any of the above steps didn't run correctly, then re-run the install script or selectively re-run the failing commands.

Unfortunately, we will be using the `2.7` version of python. We will update this to `python3` for the next offering.

### Video
You will be streaming this video using your ABR algorithm: (https://www.youtube.com/watch?v=aqz-KE-bpKQ)
Since we're using simulation you won't be able to see the video play in real-time.
This video is encoded in the following bitrates (in Kbps):
```44 86 125 173 212 249 315 369 497 564 764 985 1178 1439 2038 2353 2875 3262 3529 3844```
Each chunk is of `4sec` duration.
The chunk sizes are declared in `real/data/videos/BigBuckBunny/trace.dat`.
We expose a video object to your abr algorithm (see `your_code/video.py`) for you to read this video metadata easily.

### Traces
We've provided you with few sample traces in `network/traces/cellular` folder for you to run simple experiments with your ABR algorithm.
We've also provided a much larger set of traces which we call for you to do a more thorough evaluation.
All of these traces will be downloaded and placed in the right folders in the setup phase after you've run `install.sh`.
If you think this didn't happen for you then look for the commands that download these traces towards the end of `install.sh`

 1. **hsdpa**:
   - 4G traces taken from [http://home.ifi.uio.no/paalh/dataset/hsdpa-tcp-logs/](http://home.ifi.uio.no/paalh/dataset/hsdpa-tcp-logs/)
   - These traces can be found in `network/traces/hsdpa`
   - This dataset is split into three parts `train`, `valid` and `test` for your evaluation.
   - There are 30 traces in `train`,  8 in `valid` and 9 in  `test`
 2. **fcc**:
   - Bandwidth traces taken from [https://www.fcc.gov/general/measuring-broadband-america](https://www.fcc.gov/general/measuring-broadband-america)
   - These traces can be found in `network/traces/fcc`
   - This dataset is split into three parts `train`, `valid` and `test` for your evaluation.
   - There are 50 traces in `train`, and 10 each in `valid` and `test`

Please don't try to overfit to the `test` traces for the above datasets.
We have another set of heldout traces which will be used for the leaderboard and final evaluation.

Some of these traces might have a very high or very low average throughput. You might want to rescale it to a
more reasonable value for ABR say somewhere between 300 Kbps and 4 Mbps.
In order to scale a trace down to the desired average throughput we provide you with the `network/scale_trace.py` script.
Please don't modify the `network/traces` directory; instead, make a separate directory for traces that you scale yourself.
For example, to scale a trace to 2Mbps rescaled trace from `network/traces/cellular/Verizon1.dat`, run:
```
mkdir -p netowrk/traces/scaled_traces
python network/scale_trace.py --trace-in network/traces/cellular/Verizon1.dat --trace-out /tmp/test.txt --target-mbps=2
```
Please note that it is not possible to achieve scaling with 100% accuracy due to discrete packet effects.
Also, since the trace duration is unknown, the avg throughput of the actual trace duration seen might be different from the actual scaled value.

### Your task

You will only have to modify `your_code/abr.py`, the class that implements your ABR algorithm.

This class is instantiated with the ABR server and has access to both a `Video` and `Objective` object. The `Video` gives you
information about the videos available bitrates and chunk sizes for all video chunks. The `Objective` is your interface to the
Quality of Experience (QoE) metric you'll use to judge how "good" your algorithm is. Recall from class that the QoE for a chunk
is:
```
QoE(e_i) = P(e_i) - a * R(e_i) - b * |P(e_i) - P(e_{i-1})| - c * R(e_0)
```
where:
 - e_i is the bitrate of the i-th chunk
 - P(e_i) is the perceptual quality of the chunk. For your experiments, P(e_i) = 100 * e_i / max{e_i}, i.e. it is on a scale of 0 - 100.
 - R(e_0) is the delay between loading the video player and playing the first chunk
 - R(e_i) for i > 0 is the rebuffering time required to play the i-th chunk
 - a is the rebuffering penalty, which is set to 25. This means that rebuffering for 4 seconds negates the value of playing a single high-quality chunk.
 - b is the smoothness penalty, which is set to 1.
 - c is the startup delay, which is 5.

You must fill out the `next_quality(..)` function in the `ABR` class.
Read the comments in `abr.py`, `video.py`, and `objective.py` to understand what information is available to you. You may use this information however you'd like in your ABR algorithm. Please do **not** modify `video.py` or `objective.py`.

A reference rate based abr algorithm is provided for your reference in `your_code/rb.py`.
Please refer to it before you start implementing your own algorithm.

### Running experiments

Over the course of developing an ABR algorithm you would be required to evaluate your algorithm in single trace mode and batched mode.

**Single trace:**

In this case, you are evaluating your algorithm on just a single trace. This is helpful when you're trying to study the behavior of your algorithm on a single interesting case.

In order to run an experiment with your ABR algorithm on the trace `network/traces/cellular/Verizon1.dat` use the following command:
```python sim/run_exp.py -- --mm-trace=network/traces/cellular/Verizon1.dat --results-dir=${results_dir}```
For instance, if you specify `results/test` for the `results_dir` argument then you should be able to find the following files there on a successful run under `results/test` directory:
* `buffer-bitrate-throughput.png` : Plots buffer size, bitrates fetched by abr and link capacity in a single plot
* `qoe_plot.png`: Plots different components of the QoE objective.
* `results.json`: Aggregate QoE metrics for the run.
* `qoe.txt`: Chunk-by-chunk breakdown of the qoe objective achieved

**Batched mode:**
In this case you are evaluating your algorithm on a relatively large set of traces. This is helpful when you would like to perform a comprehensive evaluation on a set of traces.
For this, you would need to split the dataset of traces into `train`, `valid` and `test` sets. We already provide you with these splits for `hsdpa` and `fcc` traces in `network/traces/` directory.

To evaluate your algorithm in batched mode run the following command:
```python scripts/run_exps.py --name=batch_eval_1 --trace_set=fcc --n_train_runs=16 --n_valid_runs=8 --n_test_runs=8 --results_dir=results/```

This will sample a random set of 16 traces (with replacement) from `network/traces/fcc/train` and 8 from `network/traces/fcc/valid` and 8 from `network/traces/fcc/test`.
It would scale these traces so that their average throughput is in the range from `300 Kbps` to `4 Mbps`.
It would kick-off experiments on these traces in parallel and dump the results into the specified `results_dir/batch_eval_1`.

**CDFs:**
In order to compare different abr algorithms on different sets of traces, we give you the script `scripts/plt_cdf.py` to plot multiple runs together in a CDF.
For instance, if you have used the above batched mode command to create two runs `batch_eval_1` and `batch_eval_2` in `results` folder, then use the following to plot the cdf of qoe values:
```python scripts/plt_cdf.py --runs batch_eval_1 batch_eval_2```
If this was successful, you will see the plot in the file `cdfs/batch_eval_1_batch_eval_2/*.png`
For example CDFs comparing robust-mpc, buffer-based and rate-based schemes on hsdpa train dataset see the figure in [figures/hsdpa.png](figures/hsdpa.png).

## Submission

Your writeup for the entire problem set (problems 1 and 2) should be placed in WRITEUP.{md,pdf,txt}. Use this Google form  to upload a link to your repository: https://forms.gle/6eteYLQ4xbrZJFWT6
Your repository must be cloned from this starter repository. Ensure that the usernames "aravic" and "venkatarun95" are added as collaborators to your repository if you are using github.com. Alternatively, if you are using github.mit.edu, please ensure that the usernames "addanki" and "venkatar" are added.

We will only consider commits made before the submission deadline. If you would like to use an extension day, include the string "EXTENSION-DAY" in  _all_  commit messages for commits made after the deadline AND contact the staff individually once you are done committing. You must submit the form (which tells us where your repository is) before the original deadline, even if you are using extension days. Extension days cannot be used for contest submissions.

The first part of problem 2 in this of the assignment asks you to implement a buffer-based (BB) scheme. We don't expect code to be turned in for this part, only a writeup of your answers.

The second part of problem 2 asks you to come up with your own algorithm, your goal being to get a better average QoE than BB. Like PS2, we will provide a leaderboard for submissions, which will be opened a few days after the problem set is released. Please note that:
1. Your leaderboard rank has **very little** weightage for your grade
2. The leaderboard server will execute your code locally. It will show the results produced in your local development environment. We therefore ask that you act in good faith and don't modify the submission code.

To submit to the leaderboard, run:
```
Coming soon.....
```
After the final submission deadline, we will run all submissions on heldout traces that are not available to you
(to discourage overfitting to the provided traces). Your grade on this part of the problem set will be from this final run.

## Rough Grading Scheme

Please note that the leaderboard is provided so that you can compare the performance of your algorithm against others. It will be given a very **little** weightage when calculating your grade.
What is far more important is your write-up.
A large portion of the grade is assigned to the design and the choice of the algorithm that you've used.
Please indicate your rationale that went into your ABR algorithm. Include a brief report of all the ideas that you've tried.
Include results from an evaluation done locally on a set of relevant traces of your choosing. Include CDFs that compare your approach against buffer-based approach on the given set of traces.
How did your evaluation guide you to come up with better ideas for ABR? What worked and what didn't?
Detail which parts of your algorithm are novel and which are similar to already existing algorithms covered in the class or that you're familiar with.

## Honor code
By submitting to the leaderboard you agree to abide by the following non-exclusive code of conduct:
 - You agree not to overfit to the held-out traces. These traces should only be used for leaderboard submissions.
 - You agree not to launch adverserial attacks or requests on to the leaderboard server
 - You agree not to submit to the leaderboard by modifying the parameters used in the QoE objective function (smoothness penalty, rebuffering penalty etc,.)

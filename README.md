# Designing ABR Algorithms

## Introduction

After her successful stint at Massive Internet Transfers, Alyssa P. Hacker was hired as
CTO of Multinational Internet Television, a company that streams on-demand TV
shows to users. The company is facing a critical problem: users on cellular
connections have a terrible streaming experience: their video is either too low
quality or they rebuffer too often.
As her first hire, you've been tasked with implementing an ABR scheme to
maximize the
Quality of Experience for users on cellular connections. 

For this part of the assignment, you will be writing ABR (adaptive bitrate) algorithms and viewing the results
on an actual video in your browser. The lab uses the [Dash.js](https://github.com/Dash-Industry-Forum/dash.js/wiki)
open-source video client, which implements the [DASH](https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP)
(Dynamic Adaptive Streaming over HTTP) standard. Fortunately, you won't need to touch Javascript for this lab; you will
be coding entirely in Python.

## The Code

### Running experiments

You'll be running the video over a link that emulates a cellular trace with deep buffers,
using [Mahimahi](mahimahi.mit.edu). Your video client
(e.g. your browser) runs inside the Mahimahi link shell, while the video server lies outside the shell. You may choose from
the cellular traces in the `traces/` directory. 

A typical ABR algorithm would be written in Javascript as part of Dash.js. For this lab, we've abstracted this away with
an ABR server in `abr_server.py`, which also runs inside the Mahimahi shell. You'll be modifying `abr.py`, which the ABR
server calls to do the actual bitrate-choosing logic. You shouldn't modify any other file for this lab.

To run an experiment, choose a trace and scale it down to the desired average
throughput before running. For example, to scale a trace to 2Mbps, run:
```
mkdir -p scaled_traces
python scale_trace.py --in=traces/Verizon1.dat --out=scaled_traces/Verizon1.dat 2
python run_exp.py --mm-trace=scaled_traces/Verizon1.dat
```
This launches the video server and a Mahimahi link shell that runs an ABR server, throughput server (which serves link
capacity information; you don't need to worry about this), and a Chrome browser. The page it navigates to will play the
video and show you a live graph with the current link capacity (shaded region), most recently fetched bitrate (red) and
current buffer level (blue). The ABR server logs the QoE information and displays the average QoE once the video is finished.

### Your task

You will only have to modify `abr.py`, the class that implements your ABR algorithm.

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
Read the comments in `abr.py`, `video.py`, and `objective.py` to understand what information is available to you. You may use
this information however you'd like in your ABR algorithm. Anything you print will appear in `logs/abr_server.log`

## Setup

We _highly_ recommend you use a Linux machine or VM with a GUI so that you can actually watch the video.
If you don't have access to one, the repo provides a Vagrantfile (see below).

### Custom machine

The dependencies are mininal. You must have python 2.7 (callable with `python`), Google Chrome v59 or higher (callable with `google-chrome`),
and mahimahi installed (callable with `mm-link` and `mm-delay`). If you're missing any of these, copy the setup commands in the Vagrantfile.

Once you have finished, download the video you'll be using:
```
cd server/data/videos
wget 6829fa18.csail.mit.edu:8080/BigBuckBunny.tar.gz
tar -xzvf BigBuckBunny.tar.gz
rm BigBuckBunny.tar.gz
```

### Vagrant

If you choose to use Vagrant, first clone this repository.
Then, install [Vagrant](https://www.vagrantup.com/) and [Virtualbox](https://www.virtualbox.org/) and run `vagrant up`.
The [vagrant-faster plugin](https://github.com/rdsubhas/vagrant-faster) may be useful for you.
The Vagrantfile has been setup for you to use the GUI. After accessing the machine with `vagrant ssh`,
run `startx` to start the GUI.

## Submission

The first part of the assignment asks you to implement a buffer-based (BB) scheme. We don't expect code to be turned in for this part, only a writeup of your answers.

The second part asks you to come up with your own algorithm, your goal being to get a better average QoE than BB. Like PS2, we
will provide a leaderboard for submissions. Please note that your grade on the assignment does **not** depend on your leaderboard rank!
To submit to the leaderboard, run:
```
python run_submit.py
```
This will run the video locally on one of the traces we've provided you, and then publish the results to the leaderboard.

After the final submission deadline, we will run all submissions on a different cellular trace that is not available to you
(to discourage overfitting to the provided traces). Your grade on this part of the problem set will be from this final run.




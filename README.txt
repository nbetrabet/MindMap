MindMap git repo

Usage:

The two main functionalities of the Mind Map system are as follows:
	-Sample real-time EEG signal data and write that data to a file with classification labels
	-Feed the sampled EEG signal data to the trained ML model for real-time classification

These functionalities are shown using the following scripts and run as such:
	-ad_file_dump.py -> Dumps a 5 second clip of EEG data with classification labels to a csv file as specified within the script
	python3 ad_file_dump.py

	-ad_pred.py -> In real-time, feeds sampled EEG signals to a secondary process which loads the trained model and uses the sampled EEG data to predict whether motion occurs
	python3 ad_pred.py
		-this script is dependent upon par_inference.py which is imported to the main script and then spawned as a parallel process with a queue acting as the go-between for the EEG data

In addition to these main scripts, we have our ML model training script
	-lda_dump.py -> trains the LDA model using training data in /train/* and dumps the joblib file with the trained model parameters

	-lda_plot.py -> Trains LDA model but calculates accuracy scores at each step and plots the accuracy as a function of the number of samples fitted

	-plot_data.py -> Plots a 100 sample slice of collected EEG data



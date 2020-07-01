import tensorflow as tf
import settings
from preprocessor import preprocess_subject
from training import *
from predict import *
from options import test_opt
from dataset_splitter import _test_generate_train_valid_test_, generate_train_valid_test_mr


def train(training_generator, validation_generator, opt=test_opt(None), str_arch='gru_arch_general4'):
    """
    See bcg_net.py for inspiration.  The extra thing to consider is that
    it would be nice to be able to switch between CNN and RNN which require
    fundamentally different data restructuring {- maybe - this could go in
    the architecture but probably there is some reason I have not thought
    about it, for why this doesn’t work }. I have example code for this,
    but may not be in bcg_net.

    :param d_features:
    :param opt:
    :return:
    """
    # Tensorflow session configuration
    if int(tf.__version__[0]) > 1:
        session_config = tf.compat.v1.ConfigProto(gpu_options=tf.compat.v1.GPUOptions(allow_growth=True))
        sess = tf.compat.v1.Session(config=session_config)
    else:
        session_config = tf.ConfigProto(gpu_options=tf.GPUOptions(allow_growth=True))
        sess = tf.Session(config=session_config)

    # Obtain the model and callback
    model = get_arch_rnn(str_arch, opt.lr)
    callbacks_ = get_callbacks_rnn(opt)

    # Fitting the model
    m = model.fit_generator(generator=training_generator, epochs=opt.epochs, verbose=2, callbacks=callbacks_,
                            validation_data=validation_generator)

    epochs = len(m.epoch)

    return model, callbacks_, m, epochs


def predict(model, callbacks_, vec_normalized_raw_dataset, vec_raw_dataset, vec_orig_sr_raw_dataset, vec_ecg_stats,
            vec_eeg_stats, opt, vec_good_idx):
    """
    TODO: Write doc

    :return:
    """
    # Predict the cleaned dataset and epoch it for comparison later
    vec_orig_sr_epoched_cleaned_dataset, vec_orig_sr_cleaned_dataset, vec_epoched_cleaned_dataset, \
    vec_cleaned_dataset = predict_time_series_mr(model, callbacks_, vec_normalized_raw_dataset, vec_raw_dataset,
                                                 vec_orig_sr_raw_dataset, vec_ecg_stats, vec_eeg_stats,
                                                 opt.epoch_duration, vec_good_idx)

    return vec_orig_sr_epoched_cleaned_dataset, vec_orig_sr_cleaned_dataset, vec_epoched_cleaned_dataset, \
           vec_cleaned_dataset


def clean():
    """

    :return:
    """
    return


def _test_train_(str_sub, vec_run_id, str_arch='gru_arch_general4', opt=test_opt(None)):
    if not isinstance(vec_run_id, list):
        if isinstance(vec_run_id, int):
            vec_run_id = [vec_run_id]
        else:
            raise Exception("Unsupported type; vec_run_id must be a list or an int.")

    # Generate the train, validation and test sets and also obtain the index of epochs used in the validation
    # and test set
    mr_combined_xs, mr_combined_ys, mr_vec_ix_slice, mr_ten_ix_slice = _test_generate_train_valid_test_(str_sub,
                                                                                                        vec_run_id)
    # Obtain the training and validation generators
    training_generator = Defaultgenerator(mr_combined_xs[0], mr_combined_ys[0], batch_size=opt.batch_size, shuffle=True)
    validation_generator = Defaultgenerator(mr_combined_xs[1], mr_combined_ys[1], batch_size=opt.batch_size,
                                            shuffle=True)
    model, callbacks_, m, epochs = train(training_generator, validation_generator, opt, str_arch)
    return model, callbacks_, m, epochs


def _test_predict_(str_sub, vec_run_id, str_arch='gru_arch_general4', opt=test_opt(None)):
    if not isinstance(vec_run_id, list):
        if isinstance(vec_run_id, int):
            vec_run_id = [vec_run_id]
        else:
            raise Exception("Unsupported type; vec_run_id must be a list or an int.")

    # Preprocess
    # Load, normalize and epoch the raw dataset from all runs
    vec_normalized_epoched_raw_dataset, vec_normalized_raw_dataset, vec_epoched_raw_dataset, vec_raw_dataset, \
    vec_orig_sr_epoched_raw_dataset, vec_orig_sr_raw_dataset, vec_ecg_stats, vec_eeg_stats, vec_good_idx \
        = preprocess_subject(str_sub, vec_run_id)
    mr_combined_xs, mr_combined_ys, mr_vec_ix_slice, mr_ten_ix_slice \
        = generate_train_valid_test_mr(vec_normalized_epoched_raw_dataset, vec_run_id, opt=opt)
    # Obtain the training and validation generators
    training_generator = Defaultgenerator(mr_combined_xs[0], mr_combined_ys[0], batch_size=opt.batch_size, shuffle=True)
    validation_generator = Defaultgenerator(mr_combined_xs[1], mr_combined_ys[1], batch_size=opt.batch_size,
                                            shuffle=True)
    model, callbacks_, m, epochs = train(training_generator, validation_generator, opt, str_arch)

    """
    Prediction
    """
    vec_orig_sr_epoched_cleaned_dataset, vec_orig_sr_cleaned_dataset, vec_epoched_cleaned_dataset, vec_cleaned_dataset \
        = predict(model, callbacks_, vec_normalized_raw_dataset, vec_raw_dataset, vec_orig_sr_raw_dataset,
                  vec_ecg_stats, vec_eeg_stats, opt, vec_good_idx)

    return vec_orig_sr_epoched_cleaned_dataset, vec_orig_sr_cleaned_dataset, vec_epoched_cleaned_dataset, \
           vec_cleaned_dataset


if __name__ == '__main__':
    """ used for debugging """
    from pathlib import Path

    settings.init(Path.home(), Path.home())  # Call only once
    _test_train_(str_sub='sub11', vec_run_id=1)
    _test_predict_(str_sub='sub11', vec_run_id=1)

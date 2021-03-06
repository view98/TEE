# coding=utf-8
import argparse
import logging
import os
import random

import numpy as np
import torch

from datasets import load_datasets_and_vocabs
from models import TEE_GAT_Event
from trainer import train

logger = logging.getLogger(__name__)


def set_seed(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)


def parse_args():
    parser = argparse.ArgumentParser()

    # Required parameters
    parser.add_argument('--dataset_path', type=str, default='./data', help='Dataset path.')
    parser.add_argument('--dataset_name', type=str, default='CoNLL2009_Chinese',help='Choose CoNLL2009 Chinese dataset.')
    parser.add_argument('--output_dir', type=str, default='./output', help='Directory to store output data.')
    parser.add_argument('--num_classes', type=int, default=2, help='Number of classes of topic event.')
    parser.add_argument('--seed', type=int, default=2020, help='random seed for initialization')
    parser.add_argument('--cuda_id', type=str, default='0', help='Choose which GPUs to run')

    # Model parameters
    parser.add_argument('--embedding_dir', type=str, default='./model/word2vec', help='Directory storing embeddings')
    parser.add_argument('--embedding_type', type=str, default='word2vec',help='Embedding type')
    parser.add_argument('--embedding_dim', type=int, default=128, help='Dimension of embeddings')
    parser.add_argument('--dep_embedding_dim', type=int, default=128, help='Dimension of dependency embeddings')
    parser.add_argument('--pos_embedding_dim', type=int, default=128, help='Dimension of pos embeddings')
    parser.add_argument('--sen_order_embedding_dim', type=int, default=128, help='Dimension of role embeddings')

    #Bi-LSTM
    parser.add_argument('--hidden_size', type=int, default=200,help='Hidden size of bilstm, in early stage.')
    parser.add_argument('--num_layers_bilstm', type=int, default=4,
                        help='Number of layers of bilstm.')

    # MLP
    parser.add_argument('--num_mlps', type=int, default=4, help='Number of mlps in the last of model.')
    parser.add_argument('--final_hidden_size', type=int, default=200, help='Hidden size of mlps.')

    #GAT
    parser.add_argument('--num_heads', type=int, default=6, help='Number of heads for gat.')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout rate for embedding.')
    parser.add_argument('--alpha', type=float, default=0.2, help='Alpha for the leaky_relu.')
    parser.add_argument('--num_token_gat_layers', type=int, default=1, help='Number of GAT layers.')
    parser.add_argument('--num_dep_event_gat_layers', type=int, default=1, help='Number of dependency GAT layers.')
    parser.add_argument('--num_org_event_gat_layers', type=int, default=1, help='Number of organization GAT layers.')
    parser.add_argument('--num_share_event_gat_layers', type=int, default=1, help='Number of share GAT layers.')


    # Training parameters
    parser.add_argument("--per_gpu_train_batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--per_gpu_eval_batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument('--gradient_accumulation_steps', type=int, default=2,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument("--learning_rate", default=8e-4, type=float,
                        help="The initial learning rate for Adam.")
    parser.add_argument("--num_train_epochs", default=10.0, type=float,
                        help="Total number of training epochs to perform.")
    parser.add_argument("--max_steps", default=-1, type=int,
                        help="If > 0: set total number of training steps(that update the weights) to perform. Override num_train_epochs.")
    parser.add_argument('--logging_steps', type=int, default=5,
                        help="Log every X updates steps.")


    return parser.parse_args()


def check_args(args):
    '''
    eliminate confilct situations
    '''
    logger.info(vars(args))


def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s', datefmt='%m/%d/%Y %H:%M:%S',level=logging.INFO)

    # Parse args
    args = parse_args()
    check_args(args)

    # Setup CUDA, GPU training
    os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda_id
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    device = 'cpu'
    args.device = device
    logger.info('Device is %s', args.device)

    # Set seed
    set_seed(args)

    # Load datasets and vocabs
    train_dataset,train_labels_weight, test_dataset,test_labels_weight, word_vocab, dep_tag_vocab, pos_tag_vocab,sen_id_tag_vocab = load_datasets_and_vocabs(args)

    # Build Model
    model = TEE_GAT_Event(args, dep_tag_vocab['len'], pos_tag_vocab['len'],sen_id_tag_vocab['len'])

    model.to(args.device)
    # Train
    _, _, all_eval_results = train(args, train_dataset, train_labels_weight, model, test_dataset,test_labels_weight)

    if len(all_eval_results):
        best_eval_result = max(all_eval_results, key=lambda x: x['acc'])
        for key in sorted(best_eval_result.keys()):
            logger.info("  %s = %s", key, str(best_eval_result[key]))

if __name__ == "__main__":
    main()


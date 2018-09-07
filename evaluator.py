from gensim.models import KeyedVectors
import pickle
import os
import pandas as pd

import sys
sys.path.insert(0, '../common/')
import common


class Evaluator(object):

    def __init__(self, tokens):
        self.tokens = tokens

    @classmethod
    def from_storage(cls, tokens_path):
        tokens = common.read_pickle(tokens_path)
        return cls(tokens)

    @staticmethod
    def _convert_into_gensim_format(matrix_path):
        gensim_word_vectors_path = matrix_path.split('.')[0] + '_embeddings.csv'
        with open(matrix_path) as matrix:
            with open(gensim_word_vectors_path, 'w') as output:
                vector = matrix.readline()
                dimension = len(vector.split(','))
                output.write(str(len(tokens)) + ' ' + str(dimension) + '\n')  # First line
                vector = vector.replace(',', ' ')
                output.write(tokens[0] + ' ' + vector)  # Second line
                for i in range(1, len(tokens)):
                    vector = matrix.readline()
                    vector = vector.replace(',', ' ')
                    output.write(tokens[i] + ' ' + vector)
        gensim_word_vectors = KeyedVectors.load_word2vec_format(gensim_word_vectors_path).wv
        return gensim_word_vectors

    def evaluate(self, matrix_path):
        gensim_word_vectors = self._convert_into_gensim_format(matrix_path)

        # evaluation results
        labels1, results1 = self.evaluation_questions_words(gensim_word_vectors)
        # self.print_lables_results(labels1, results1)
        labels2, results2 = self.evaluation_word_pairs(gensim_word_vectors, evaluation_data_path='data/wordsim353/combined.tab')
        # eval.print_lables_results(labels2, results2)
        labels3, results3 = self.evaluation_word_pairs(gensim_word_vectors, evaluation_data_path='data/simlex999.txt')
        # eval.print_lables_results(labels3, results3)
        return results2 + results3 + results1

    @staticmethod
    def print_lables_results(labels, results):
        if len(labels) != len(results):
            print('[ERROR] labels and results do not have the same length')
            exit()
        to_print = ''
        for i in range(len(labels)):
            to_print += labels[i] + ': ' + str(results[i]) + ';\t'
        print(to_print)

    @staticmethod
    def evaluation_questions_words(gensim_word_vectors, evaluation_data_path='data/questions-words.txt'):
        accuracy = gensim_word_vectors.accuracy(evaluation_data_path)  # 4478

        sem_correct = sum((len(accuracy[i]['correct']) for i in range(5)))
        sem_total = sum((len(accuracy[i]['correct']) + len(accuracy[i]['incorrect'])) for i in range(5))
        sem_acc = 100 * float(sem_correct) / sem_total

        syn_correct = sum((len(accuracy[i]['correct']) for i in range(5, len(accuracy) - 1)))
        syn_total = sum((len(accuracy[i]['correct']) + len(accuracy[i]['incorrect'])) for i in range(5, len(accuracy) - 1))
        syn_acc = 100 * float(syn_correct) / syn_total

        sum_corr = len(accuracy[-1]['correct'])
        sum_incorr = len(accuracy[-1]['incorrect'])
        total = sum_corr + sum_incorr
        total_acc = sum_corr / total * 100

        labels = ['sem_acc', '#sem', 'syn_acc', '#syn', 'total_acc', '#total']
        results = [sem_acc, sem_total, syn_acc, syn_total, total_acc, total]
        return labels, results

    @staticmethod
    def evaluation_word_pairs(gensim_word_vectors, evaluation_data_path):
        """ Result of evaluate_word_pairs contains 3 parts:
        ((0.43915524919358867, 2.3681259690228147e-13),                                     Pearson
        SpearmanrResult(correlation=0.44614214937080449, pvalue=8.8819867392097872e-14),    Spearman
        28.328611898016998)                                                                 ratio of pairs with unknown
                                                                                            words (float)
        """
        evaluation = gensim_word_vectors.evaluate_word_pairs(evaluation_data_path)
        labels = ['Pearson correlation', 'Pearson pvalue', 'Spearman correlation', 'Spearman pvalue',
                  'Ration of pairs with OOV']
        results = [evaluation[0][0], evaluation[0][1], evaluation[1][0], evaluation[1][1], evaluation[2]]
        return labels, results

    def evaluate_all_word_embeddings_files_in_folder(self, folder_path, excel_path):
        # Get all files ends with '.csv'
        files = [os.path.join(folder_path, name) for name in os.listdir(folder_path)
                 if (os.path.isfile(os.path.join(folder_path, name))
                     and name.endswith('.csv'))]
        df = pd.DataFrame(columns=[
            # word embeddings file name
            'file name',
            # wordsim353
            'wordsim353_Pearson correlation', 'Pearson pvalue',
            'Spearman correlation', 'Spearman pvalue', 'Ration of pairs with OOV',
            # simlex999
            'simlex999_Pearson correlation', 'Pearson pvalue',
            'Spearman correlation', 'Spearman pvalue', 'Ration of pairs with OOV',
            # questions-words
            'sem_acc', '#sem', 'syn_acc', '#syn', 'total_acc', '#total'
        ])
        i = 0
        for file in files:
            temp = [file] + self.evaluate(file)
            df.loc[i] = temp
            print(temp)
            i += 1
        writer = pd.ExcelWriter(excel_path)
        df.to_excel(writer, 'Sheet1')
        writer.save()


def get_index2word(file, key_type=int, value_type=str):
    """ATTENTION
    This function is different from what in graph_data_provider.
    Here, key is id and token is value, while in graph_data_provider, token is key and id is value.
    """
    d = {}
    with open(file, encoding='utf-8') as f:
        for line in f:
            (key, val) = line.rstrip('\n').split("\t")
            d[key_type(val)] = value_type(key)
        return d


if __name__ == '__main__':
    # Adapted to the result of corpus2graph
    word_ids_path = '/Users/zzcoolj/Desktop/GoW_new_ideas/input/cooccurrence matrix/encoded_edges_count_window_size_5_undirected_nodes.pickle'
    merged_dict_path = '/Users/zzcoolj/Desktop/GoW_new_ideas/input/dict_merged.txt'
    wordId2word = get_index2word(file=merged_dict_path)
    with open(word_ids_path, 'rb') as fp:
        word_ids = pickle.load(fp)
    tokens = [wordId2word[wordId] for wordId in word_ids]

    # # This blocked code is for generating tokens file corresponding to the negative examples matrix
    # with open("/Users/zzcoolj/Desktop/ns/random walk/random_walk_tokens.txt", 'w') as resultFile:
    #     for token in tokens:
    #         resultFile.write(token+'\n')
    # exit()

    e = Evaluator(tokens=tokens)
    e.evaluate_all_word_embeddings_files_in_folder(folder_path='/Users/zzcoolj/Desktop/GoW_new_ideas/embeddings/new/',
                                                   excel_path='/Users/zzcoolj/Desktop/GoW_new_ideas/embeddings/new/plus.xlsx')

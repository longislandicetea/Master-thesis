#!/usr/bin/python
# -*- coding: utf-8 -*-

# authority propagation with BibRank
# Author: Hao Luo

import numpy as np
from sklearn.preprocessing import normalize

import file_io as fio

class BibRank(object):
	def __init__(self, expert_finder, topic_label, hin,
				 eps_d=0.15, eps_a=0.15, eps_v=0.15,
				 gamma_da=1.0/3, gamma_dv=1.0/3, gamma_dd=1.0/3,
				 gamma_ad=1.0/2, gamma_aa=1.0/2,
				 average_prop=False
				 ):
		# propagation factor should sum up to 1
		assert gamma_da + gamma_dv + gamma_dd == 1.0
		assert gamma_ad + gamma_aa == 1.0
		self.eps_d, self.eps_a, self.eps_v = eps_d, eps_a, eps_v
		self.gamma_da, self.gamma_dv, self.gamma_dd = gamma_da, gamma_dv, gamma_dd
		self.gamma_ad, self.gamma_aa = gamma_ad, gamma_aa
		self.topic_label = topic_label

		# reference to global hin
		self.hin = hin

		# initial topical rank scores of papers, authors and venues
		# two strategies: 
		#    1) either 1 or 0 
        #    2) topical ranking distributino inferred from ExpertFinder
		self.init_rank_papers = normalize(np.array([1.0 if z == topic_label else 0.0 
									      			for z in expert_finder.z_d]),
										  norm='l1').transpose()
		self.init_rank_authors = normalize(expert_finder.dist_z_a[topic_label], norm='l1').transpose()
		self.init_rank_venues = normalize(expert_finder.dist_z_v[topic_label], norm='l1').transpose()

		# test
		'''self.init_rank_papers = normalize(np.ones(len(expert_finder.z_d)), norm='l1').transpose()
		self.init_rank_authors = normalize(np.ones(6), norm='l1').transpose()
		self.init_rank_venues = normalize(np.array([1000.0, 20.0, 1.0]), norm='l1').transpose()
		print "initial authors: ", self.init_rank_authors
		print "initial venues: ", self.init_rank_venues'''

		# iterative rank scores of papers, authors and venues
		self.rank_papers = self.init_rank_papers
		self.rank_authors = self.init_rank_authors
		self.rank_venues = self.init_rank_venues

	def run(self):
		last_rank_papers = self.rank_papers
		self.rank_papers = self.eps_d * self.init_rank_papers + \
						   (1 - self.eps_d) * (self.gamma_da * self.hin.m_d_a.dot(self.rank_authors) + 
						   					   self.gamma_dv * self.hin.m_d_v.dot(self.rank_venues) + 
						   	                   self.gamma_dd * self.hin.m_d_d.dot(last_rank_papers))
		self.rank_authors = self.eps_a * self.init_rank_authors + \
							(1 - self.eps_a) * (self.gamma_ad * self.hin.m_a_d.dot(last_rank_papers) + 
								                self.gamma_aa * self.hin.m_a_a.dot(self.rank_authors))
		self.rank_venues = self.eps_v * self.init_rank_venues + \
						   (1 - self.eps_v) * self.hin.m_v_d.dot(last_rank_papers)

def format_list(lst, num_col):
	num_row = len(lst) / num_col
	return '\n'.join([(' '.join([str(round(x,3)) for x in lst[i*num_col:(i+1)*num_col]])) for i in xrange(num_row)])

def propagte_with_bibrank(bibrank, iteration):
	print "Topic {i} Bibrank propagating...".format(i=bibrank.topic_label)
	for i in xrange(iteration):
		print 'iter: ', i
		fio.log_topical_ranking(
			dist_arr=bibrank.rank_authors, 
			log_type='author', 
			topic_label=bibrank.topic_label, 
			idx_name_dict=None, 
			iter_id=i)
		fio.log_topical_ranking(
			dist_arr=bibrank.rank_venues, 
			log_type='venue', 
			topic_label=bibrank.topic_label, 
			idx_name_dict=None, 
			iter_id=i,
			topn=23)
		bibrank.run()
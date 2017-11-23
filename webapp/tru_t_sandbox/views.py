from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings

import glob
import os
import json
import sys

sys.path.append(settings.BACKEND_SRC)

import reaction_factories
import process_single

# this is where the models are stored:
MODELS_DIR = settings.MODELS_DIR
MODEL_SUFFIX = settings.MODEL_SUFFIX

CUSTOM_MODELS_DIR = settings.CUSTOM_MODELS_DIR

def get_available_models():
        model_files = glob.glob(os.path.join(MODELS_DIR, '*' + MODEL_SUFFIX))
        model_names = []
        for mf in model_files:
                model_names.append(os.path.basename(mf)[:-len(MODEL_SUFFIX)])
        return model_names


@login_required
def home_view(request):
        models = get_available_models()
        return render(request, 'home.html', {'models':models}) 


@login_required
def get_models(request):
	all_models = {}
	all_models['models'] = {}
	model_files = glob.glob(os.path.join(MODELS_DIR, '*' + MODEL_SUFFIX))
	print model_files
	for mf in model_files:
		model_name = os.path.basename(mf)[:-len(MODEL_SUFFIX)]
		rf = reaction_factories.FileReactionFactory(mf)
		this_model = {}
		this_model['name'] = model_name
		this_model['reactions'] = []
		this_model['required_initial_conditions'] = ','.join(rf.get_required_initial_conditions())
		for reaction in rf.get_reactions():
			reactants = reaction.get_reactants()
			products = reaction.get_products()
			is_bidirectional = reaction.is_bidirectional
			kf = reaction.get_fwd_k()
			kr = reaction.get_rev_k()
			reactant_str = make_equation_str(reactants)
			product_str = make_equation_str(products)
			if is_bidirectional:
				direction_str = '<--->'
			else:
				direction_str = '--->'
			reaction_dict = {}
			reaction_dict['reactants'] = reactant_str
			reaction_dict['products'] = product_str
			reaction_dict['direction'] = direction_str
			reaction_dict['kf'] = '%s' % kf
			reaction_dict['kr'] = '%s' % kr
			this_model['reactions'].append(reaction_dict)
		all_models['models'][model_name] = this_model
	#print json.dumps(all_models, sort_keys=True, indent=4, separators=(',', ': '))
	return JsonResponse(all_models)


@login_required
def single_calc(request):
	ic = request.POST.get('ic')
	ic = json.loads(ic)
	linked_model = os.path.join(CUSTOM_MODELS_DIR, request.session.get('modelfile', None))
	result = process_single.process_single(ic, linked_model)
	return JsonResponse({'result_html':result.to_frame().to_html(index_names=False, classes=['table','table-striped'])})


def write_model(factory, user, all_species):
	#TODO use the user object to make a unique model file
	filename = os.path.join(CUSTOM_MODELS_DIR, 'xyz.model')
	with open(filename, 'w') as fout:
		fout.write('#REACTIONS\n')
		for rx in factory.get_reactions():
			fout.write(rx.as_string())
			fout.write('\n')
		fout.write('#REACTIONS\n')
		fout.write('#INITIAL_CONDITIONS\n')
		for s in all_species:
			fout.write('%s=0.01\n' % s) # dummy value just to get file parser to validate
		fout.write('#INITIAL_CONDITIONS\n')
	return os.path.basename(filename)

@login_required
def validate_model(request):
	reactions = request.POST.get('reactions')
	reactions = json.loads(reactions)
	rf = reaction_factories.GUIReactionFactory(reactions)

	# get the species:
	species_set = set()
	for rx in rf.get_reactions():
		print rx
		print rx.get_all_species()
		species_set = species_set.union(rx.get_all_species())
	modelfile = write_model(rf, request.user, species_set)

	print species_set
	return_obj = {}
	return_obj['species'] = list(species_set)
	#return_obj['modelfile'] = modelfile
	request.session['modelfile'] = modelfile
	return JsonResponse(return_obj)


def make_equation_str(comps):
	comp_list = []
	for r in comps:
		coef = r.coefficient
		if coef > 1:
			comp_list.append('%s*%s' % (coef, r.symbol))
		else:
			comp_list.append(r.symbol)
	return ' + '.join(comp_list)

__author__ = 'brian'

import sys
import os

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

from src import custom_exceptions, reaction_factories
import unittest

this_dir = os.path.dirname(os.path.abspath(__file__))

class TestFileReader(unittest.TestCase):

    # tests related to the simulation time parameters

    def test_invalid_time_raises_exceptions(self):
        with self.assertRaises(custom_exceptions.InvalidSimulationTimeException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_1.txt'))

    def test_missing_time_returns_none(self):
        f = reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_2.txt'))
        self.assertEqual(f._simulation_time, None)

    # tests related to initial condition specification
    def test_missing_all_initial_conditions(self):
        with self.assertRaises(custom_exceptions.MissingInitialConditionsException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_3.txt'))

    def test_all_initial_conditions_zero_raises_exception(self):
        #TODO- threshold value?  Comparison of floats to 0 is fraught with potential errors
        # Worst case- if all are near zero, then solution just fluctuates around zero
        pass

    def test_missing_initial_condition_section(self):
        with self.assertRaises(custom_exceptions.MissingInitialConditionsException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_4.txt'))

    def test_negative_initial_condition_raises_exception(self):
        with self.assertRaises(custom_exceptions.InvalidInitialConditionException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_10.txt'))

    def test_non_number_initial_condition_raises_exception(self):
        with self.assertRaises(custom_exceptions.MalformattedReactionFileException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_8.txt'))

    def test_negative_simulation_time_raises_exception(self):
        with self.assertRaises(custom_exceptions.InvalidSimulationTimeException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_9.txt'))

    # tests related to equation section
    def test_missing_equation_section(self):
        with self.assertRaises(custom_exceptions.MalformattedReactionFileException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_5.txt'))

    def test_no_equations_raises_exception(self):
        with self.assertRaises(custom_exceptions.MalformattedReactionFileException):
            reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_6.txt'))

    def test_missing_line_ignored(self):
        f = reaction_factories.FileReactionFactory(os.path.join(this_dir,'test_model_7.txt'))
        all_reactions = f.get_reactions()
        self.assertEqual(len(all_reactions),2)

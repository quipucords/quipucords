import React from 'react';
import AddSourceWizardStepOne from './addSourceWizardStepOne';
import AddSourceWizardStepTwo from './addSourceWizardStepTwo';
import AddSourceWizardStepThree from './addSourceWizardStepThree';

const addSourceWizardSteps = [
  {
    step: 1,
    label: '1',
    title: 'Type',
    page: <AddSourceWizardStepOne />,
    subSteps: []
  },
  {
    step: 2,
    label: '2',
    title: 'Credentials',
    page: <AddSourceWizardStepTwo />,
    subSteps: []
  },
  {
    step: 3,
    label: '3',
    title: 'Results',
    page: <AddSourceWizardStepThree />,
    subSteps: []
  }
];

const editSourceWizardSteps = [
  {
    step: 2,
    label: '1',
    title: 'Credentials',
    page: <AddSourceWizardStepTwo />,
    subSteps: []
  },
  {
    step: 3,
    label: '2',
    title: 'Results',
    page: <AddSourceWizardStepThree />,
    subSteps: []
  }
];

export { addSourceWizardSteps, editSourceWizardSteps };

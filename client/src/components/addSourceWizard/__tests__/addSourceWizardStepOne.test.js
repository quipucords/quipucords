import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import { ConnectedAddSourceWizardStepOne } from '../addSourceWizardStepOne';

describe('AddSourceWizardStepOne Component', () => {
  const generateEmptyStore = (obj = {}) => configureMockStore()(obj);

  it('should render a connected component', () => {
    const store = generateEmptyStore({ addSourceWizard: { view: {} } });
    const component = shallow(<ConnectedAddSourceWizardStepOne />, { context: { store } });

    expect(component.dive()).toMatchSnapshot('connected');
  });
});

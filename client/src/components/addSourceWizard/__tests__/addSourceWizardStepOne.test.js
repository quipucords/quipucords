import React from 'react';
import configureMockStore from 'redux-mock-store';
import { mount, shallow } from 'enzyme';
import { ConnectedAddSourceWizardStepOne, AddSourceWizardStepOne } from '../addSourceWizardStepOne';

describe('AddSourceWizardStepOne Component', () => {
  const generateEmptyStore = (obj = {}) => configureMockStore()(obj);

  it('should render a connected component', () => {
    const store = generateEmptyStore({ addSourceWizard: {} });
    const component = shallow(<ConnectedAddSourceWizardStepOne />, { context: { store } });

    expect(component.dive()).toMatchSnapshot('connected');
  });

  it('should render a non-connected component', () => {
    const props = {};

    const component = mount(<AddSourceWizardStepOne {...props} />);

    expect(component.render()).toMatchSnapshot('non-connected');
  });
});

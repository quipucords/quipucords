import React from 'react';
import { mount } from 'enzyme';
import { AddSourceWizardStepTwo } from '../addSourceWizardStepTwo';

describe('AddSourceWizardStepTwo Component', () => {
  it('should render a non-connected component', () => {
    const props = {};
    const component = mount(<AddSourceWizardStepTwo {...props} />);

    expect(component.render()).toMatchSnapshot('unconnected');
  });
});

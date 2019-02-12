import React from 'react';
import { mount } from 'enzyme';
import { AddSourceWizardStepTwo } from '../addSourceWizardStepTwo';

describe('AddSourceWizardStepTwo Component', () => {
  it('should render a non-connected component', () => {
    const props = {};
    const component = mount(<AddSourceWizardStepTwo {...props} />);

    expect(component.render()).toMatchSnapshot('unconnected');
  });

  it('should correctly validate source hosts', () => {
    expect(AddSourceWizardStepTwo.validateHosts(['l'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHost('l')).toBeNull();

    expect(AddSourceWizardStepTwo.validateHosts(['l.']).length).toBeGreaterThan(0);
    expect(AddSourceWizardStepTwo.validateHost('l.').length).toBeGreaterThan(0);

    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.0:']).length).toBeGreaterThan(0);
    expect(AddSourceWizardStepTwo.validateHost('0.0.0.0:').length).toBeGreaterThan(0);

    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.0:22']).length).toBeGreaterThan(0);
    expect(AddSourceWizardStepTwo.validateHost('0.0.0.0:22').length).toBeGreaterThan(0);

    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.[12:24]'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.[12:a]']).length).toBeGreaterThan(0);

    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/23']).length).toBeGreaterThan(0);
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/24'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/25'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/26'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/27'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/28'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/29'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/30'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/31'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/32'])).toBeNull();
    expect(AddSourceWizardStepTwo.validateHosts(['0.0.0.12/33']).length).toBeGreaterThan(0);
  });
});

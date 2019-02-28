import React from 'react';
import { mount } from 'enzyme';
import { AddSourceWizardStepTwo } from '../addSourceWizardStepTwo';

describe('AddSourceWizardStepTwo Component', () => {
  it('should render a non-connected component', () => {
    const props = {
      type: 'network'
    };

    const component = mount(<AddSourceWizardStepTwo {...props} />);

    expect(component.render()).toMatchSnapshot('non-connected');
  });

  it('should display different forms for source types', () => {
    const props = {
      type: 'network'
    };

    let component = mount(<AddSourceWizardStepTwo {...props} />);
    expect(component.render()).toMatchSnapshot('network');

    props.type = 'vcenter';
    component = mount(<AddSourceWizardStepTwo {...props} />);
    expect(component.render()).toMatchSnapshot('vcenter');
  });

  it('should correctly validate and submit data for sources', () => {
    const props = {
      add: true,
      type: 'network'
    };

    const spy = jest.spyOn(AddSourceWizardStepTwo.prototype, 'submitStep');
    const component = mount(<AddSourceWizardStepTwo {...props} />);
    const componentInstance = component.instance();

    expect(
      componentInstance.isStepValid({
        values: {
          credentials: [],
          hosts: [],
          name: null,
          port: -1
        }
      })
    ).toMatchSnapshot('step invalid');

    expect(
      componentInstance.isStepValid({
        values: {
          credentials: [1],
          hosts: ['0.0.0.0'],
          name: 'lorem',
          port: 22
        }
      })
    ).toMatchSnapshot('step valid');

    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should correctly validate source hosts', () => {
    expect(AddSourceWizardStepTwo.hostsValid(['l'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostValid('l')).toBe(true);

    expect(AddSourceWizardStepTwo.hostsValid(['l.'])).toBe(false);
    expect(AddSourceWizardStepTwo.hostValid('l.')).toBe(false);

    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.0:'])).toBe(false);
    expect(AddSourceWizardStepTwo.hostValid('0.0.0.0:')).toBe(false);

    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.0:22'])).toBe(false);
    expect(AddSourceWizardStepTwo.hostValid('0.0.0.0:22')).toBe(false);

    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.[12:24]'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostValid(['0.0.0.[12:a]'])).toBe(false);

    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/23'])).toBe(false);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/24'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/25'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/26'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/27'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/28'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/29'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/30'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/31'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/32'])).toBe(true);
    expect(AddSourceWizardStepTwo.hostsValid(['0.0.0.12/33'])).toBe(false);
  });
});

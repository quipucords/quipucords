import React from 'react';
import configureMockStore from 'redux-mock-store';
import { mount, shallow } from 'enzyme';
import { ConnectedAddSourceWizardStepThree, AddSourceWizardStepThree } from '../addSourceWizardStepThree';

describe('AccountWizardStepResults Component', () => {
  const generateEmptyStore = (obj = {}) => configureMockStore()(obj);

  it('should render a connected component with error', () => {
    const store = generateEmptyStore({
      addSourceWizard: {
        view: {
          source: {},
          error: true,
          errorMessage: 'Lorem ipsum'
        }
      }
    });
    const component = shallow(<ConnectedAddSourceWizardStepThree />, { context: { store } });

    expect(component).toMatchSnapshot('connected');
  });

  it('should render a wizard results step with error', () => {
    const props = {
      view: {
        add: false,
        error: true,
        errorMessage: 'lorem ipsum'
      }
    };

    let component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('error updated');

    props.view.add = true;
    component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('error created');
  });

  it('should render a wizard results step with pending', () => {
    const props = {
      view: {
        add: false,
        pending: true
      }
    };

    let component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('pending updated');

    props.view.add = true;
    component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('pending created');
  });

  it('should render a wizard results step with fulfilled', () => {
    const props = {
      view: {
        add: false,
        fulfilled: true,
        source: {
          name: 'Lorem'
        }
      }
    };

    let component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('fulfilled updated');

    props.view.add = true;
    component = mount(<AddSourceWizardStepThree {...props} />);
    expect(component).toMatchSnapshot('fulfilled created');
  });
});

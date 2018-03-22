import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import AddSourceWizard from '../addSourceWizard';

describe('AddSourceWizard Component', function() {
  const generateEmptyStore = () => configureMockStore()({ addSourceWizard: {} });

  it('should shallow render a basic component', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<AddSourceWizard {...props} />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

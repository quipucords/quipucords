import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import ScanHostList from '../scanHostList';

describe('ScanHostList Component', function() {
  const generateEmptyStore = () => configureMockStore()({});

  it('should shallow render a basic component with a basic status', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<ScanHostList {...props} status="success" />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

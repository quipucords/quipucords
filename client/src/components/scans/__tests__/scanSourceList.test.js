import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import ScanSourceList from '../scanSourceList';

describe('ScanSourceList Component', () => {
  const generateEmptyStore = () => configureMockStore()({});

  it('should shallow render a basic component with status', () => {
    const store = generateEmptyStore();
    const props = {
      scan: {
        sources: [
          {
            id: 15,
            name: 'TestSource',
            source_type: 'network'
          }
        ]
      }
    };
    const wrapper = shallow(<ScanSourceList {...props} />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

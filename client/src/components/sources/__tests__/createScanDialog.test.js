import React from 'react';
import configureMockStore from 'redux-mock-store';
import CreateScanDialog from '../createScanDialog';
import { mount } from 'enzyme';

describe('CreateScanDialog Component', function() {
  const generateEmptyStore = () => configureMockStore()({ scans: {} });

  it('should render a basic component', () => {
    const store = generateEmptyStore();
    const props = {
      show: true,
      sources: [{ name: 'test name' }]
    };

    const component = mount(<CreateScanDialog {...props} />, { context: { store } });

    expect(component.render()).toMatchSnapshot();
  });
});

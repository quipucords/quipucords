import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import MergeReportsDialog from '../mergeReportsDialog';

describe('ToastNotificationsList Component', () => {
  const generateEmptyStore = () => configureMockStore()({ scans: {} });

  it('should shallow render a basic component', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<MergeReportsDialog {...props} show details={false} scans={[{ id: 1, name: 'test' }]} />, {
      context: { store }
    });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

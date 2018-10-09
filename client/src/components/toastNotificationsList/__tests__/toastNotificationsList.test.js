import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import ToastNotificationsList from '../toastNotificationsList';

describe('ToastNotificationsList Component', () => {
  const generateEmptyStore = () => configureMockStore()({ toastNotifications: {} });

  it('should shallow render a basic component', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<ToastNotificationsList {...props} />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

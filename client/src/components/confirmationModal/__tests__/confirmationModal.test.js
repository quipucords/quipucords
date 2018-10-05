import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import ConfirmationModal from '../confirmationModal';

describe('ConfirmationModal Component', () => {
  const generateEmptyStore = () => configureMockStore()({ confirmationModal: {} });

  it('should shallow render a basic component', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<ConfirmationModal {...props} />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});

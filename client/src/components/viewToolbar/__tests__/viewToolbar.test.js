import React from 'react';
import { mount } from 'enzyme';
import ViewToolbar from '../viewToolbar';
import { viewTypes } from '../../../redux/constants';

describe('ViewPaginationRow Component', () => {
  it('should render', () => {
    const props = {
      viewType: viewTypes.SCANS_VIEW,
      totalCount: 200,
      filterFields: [
        {
          id: 'filterOne',
          title: 'Name',
          placeholder: 'Filter by Name',
          filterType: 'text'
        }
      ],
      sortFields: [
        {
          id: 'sortOne',
          title: 'Name',
          isNumeric: false
        }
      ],
      onRefresh: jest.fn()
    };

    const component = mount(<ViewToolbar {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});

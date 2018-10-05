import React from 'react';
import { mount } from 'enzyme';
import ViewPaginationRow from '../viewPaginationRow';
import { viewTypes } from '../../../redux/constants';

describe('ViewPaginationRow Component', () => {
  it('should render', () => {
    const props = {
      viewType: viewTypes.SCANS_VIEW,
      currentPage: 1,
      pageSize: 10,
      totalCount: 200,
      totalPages: 20
    };

    const component = mount(<ViewPaginationRow {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});

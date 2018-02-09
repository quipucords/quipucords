import PropTypes from 'prop-types';
import React from 'react';

import { PaginationRow, PAGINATION_VIEW } from 'patternfly-react';

import helpers from '../../common/helpers';
import Store from '../../redux/store';

import { viewPaginationTypes } from '../../redux/constants';

class ViewPaginationRow extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'onFirstPage',
      'onLastPage',
      'onPreviousPage',
      'onNextPage',
      'onPageInput',
      'onPerPageSelect'
    ]);
  }

  onFirstPage() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_FIRST_PAGE,
      viewType: viewType
    });
  }

  onLastPage() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_LAST_PAGE,
      viewType: viewType
    });
  }

  onPreviousPage() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_PREVIOUS_PAGE,
      viewType: viewType
    });
  }

  onNextPage() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_NEXT_PAGE,
      viewType: viewType
    });
  }

  onPageInput(e) {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_PAGE_NUMBER,
      viewType: viewType,
      pageNumber: parseInt(e.target.value, 10)
    });
  }

  onPerPageSelect(eventKey) {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.SET_PER_PAGE,
      viewType: viewType,
      pageSize: eventKey
    });
  }

  render() {
    const perPageOptions = [10, 15, 25, 50, 100];
    const { currentPage, pageSize, totalCount, totalPages } = this.props;

    const rowPagination = {
      page: currentPage,
      perPage: pageSize,
      perPageOptions: perPageOptions
    };

    let itemsStart = (currentPage - 1) * pageSize + 1;
    let itemsEnd = Math.min(currentPage * pageSize, totalCount);

    return (
      <PaginationRow
        viewType={PAGINATION_VIEW.LIST}
        pagination={rowPagination}
        amountOfPages={totalPages}
        itemCount={totalCount}
        itemsStart={itemsStart}
        itemsEnd={itemsEnd}
        onFirstPage={this.onFirstPage}
        onLastPage={this.onLastPage}
        onPreviousPage={this.onPreviousPage}
        onNextPage={this.onNextPage}
        onPageInput={this.onPageInput}
        onPerPageSelect={this.onPerPageSelect}
      />
    );
  }
}

ViewPaginationRow.propTypes = {
  viewType: PropTypes.string,
  currentPage: PropTypes.number,
  pageSize: PropTypes.number,
  totalCount: PropTypes.number,
  totalPages: PropTypes.number
};

export default ViewPaginationRow;

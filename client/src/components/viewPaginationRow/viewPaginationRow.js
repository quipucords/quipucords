import React from 'react';
import PropTypes from 'prop-types';
import { PaginationRow, PAGINATION_VIEW } from 'patternfly-react';
import Store from '../../redux/store';
import { viewPaginationTypes } from '../../redux/constants';

class ViewPaginationRow extends React.Component {
  onFirstPage = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_FIRST_PAGE,
      viewType
    });
  };

  onLastPage = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_LAST_PAGE,
      viewType
    });
  };

  onPreviousPage = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_PREVIOUS_PAGE,
      viewType
    });
  };

  onNextPage = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_NEXT_PAGE,
      viewType
    });
  };

  onPageInput = e => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.VIEW_PAGE_NUMBER,
      viewType,
      pageNumber: parseInt(e.target.value, 10)
    });
  };

  onPerPageSelect = eventKey => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewPaginationTypes.SET_PER_PAGE,
      viewType,
      pageSize: eventKey
    });
  };

  render() {
    const perPageOptions = [10, 15, 25, 50, 100];
    const { currentPage, pageSize, totalCount, totalPages } = this.props;

    const rowPagination = {
      page: currentPage,
      perPage: pageSize,
      perPageOptions
    };

    const itemsStart = (currentPage - 1) * pageSize + 1;
    const itemsEnd = Math.min(currentPage * pageSize, totalCount);

    return (
      <PaginationRow
        className="list-view-pagination-top"
        viewType={PAGINATION_VIEW.LIST}
        pagination={rowPagination}
        amountOfPages={totalPages}
        pageSizeDropUp={false}
        pageInputValue={currentPage}
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

ViewPaginationRow.defaultProps = {
  viewType: null,
  currentPage: 0,
  pageSize: 0,
  totalCount: 0,
  totalPages: 0
};

export { ViewPaginationRow as default, ViewPaginationRow };
